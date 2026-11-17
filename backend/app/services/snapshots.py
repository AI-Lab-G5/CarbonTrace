"""Snapshots: agregados imutaveis, gravados num momento explicito.

Quando o agregado e produzido (CA-03)
-------------------------------------
Numa chamada de escrita, `POST /v1/snapshots`, e so nela. Leitura nunca
grava -- o criterio pede isso em letra, e a razao e pratica: um GET que
grava torna o custo do Firestore imprevisivel e faz duas telas abertas
disputarem o mesmo documento.

A alternativa seria recalcular a cada leitura, que e o que o
`/v1/consolidado` do CP2 faz. Com uma rede de 30 lojas e 12 meses isso
sao milhares de documentos lidos por abertura de dashboard, e a conta de
leitura do Spark acaba antes do mes.

Como o reenvio evita duplicar (CA-03)
-------------------------------------
Cada snapshot carrega a impressao digital do seu conteudo. Gerar de novo
a mesma competencia sem nada ter mudado devolve o snapshot que ja
existe, com 200 e `criado: false` -- nao cria versao nova. Se algum
lancamento mudou, a impressao muda e nasce a versao seguinte; a anterior
fica. Snapshot nunca e editado nem apagado: e o que torna o historico
auditavel e atende "preservar snapshots anteriores" do CA-04.
"""

from __future__ import annotations

import hashlib

from app.db import colecao_do_tenant
from app.dominio.agregacao import Agregado, Lancamento, agregar
from app.dominio.numeros import como_texto, para_decimal
from app.services.autoria import agora

COLECAO = "snapshots"
SUBCOLECAO_UNIDADES = "unidades"


def id_do_snapshot(competencia: str, versao: int) -> str:
    """Identificador legivel e ordenavel.

    Zeros a esquerda porque a paginacao ordena por id como texto: sem
    eles, "v10" viria antes de "v2" e a "ultima versao" seria a errada.
    """
    return f"{competencia}_v{versao:03d}"


def impressao_digital(agregado: Agregado) -> str:
    """Resume o conteudo do agregado em 16 hex.

    Cobre o que define o snapshot: total, cada unidade e cada regiao.
    Dois agregados com a mesma impressao sao o mesmo numero publicado --
    e e isso que permite recusar uma versao nova sem conteudo novo.
    """
    partes = [f"total={como_texto(agregado.total_kg_co2e)}"]
    partes += [
        f"u:{u.unidade_id}={como_texto(u.emissao_kg_co2e)}:{u.fontes_lancadas}"
        for u in agregado.por_unidade
    ]
    partes += [
        f"r:{r.regiao}={como_texto(r.emissao_kg_co2e)}" for r in agregado.por_regiao
    ]
    partes += [
        f"e:{e.escopo}={como_texto(e.emissao_kg_co2e)}" for e in agregado.por_escopo
    ]
    return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()[:16]


def lancamentos_da_competencia(
    tenant_id: str, competencia: str
) -> list[Lancamento]:
    """Le os consumos do mes e junta com o cadastro das unidades.

    Esta e a leitura cara, e por isso acontece aqui -- uma vez, na
    geracao -- e nao a cada abertura do dashboard.
    """
    from google.cloud.firestore_v1.base_query import FieldFilter

    unidades = {
        doc.id: doc.to_dict()
        for doc in colecao_do_tenant(tenant_id, "unidades").stream()
    }

    consumos = (
        colecao_do_tenant(tenant_id, "consumos")
        .where(filter=FieldFilter("competencia", "==", competencia))
        .stream()
    )

    lancamentos = []
    for doc in consumos:
        dados = doc.to_dict()
        unidade = unidades.get(dados["unidade_id"], {})
        lancamentos.append(
            Lancamento(
                unidade_id=dados["unidade_id"],
                unidade_nome=unidade.get("nome") or dados["unidade_id"],
                # Regiao = UF, enquanto a definicao do Tech Lead (#34)
                # nao chega. Unidade sem UF nao some do total: cai em
                # "--", visivel na tela como cadastro a corrigir.
                regiao=unidade.get("uf") or "--",
                fonte_id=dados["fonte_id"],
                escopo=dados["escopo"],
                emissao_kg_co2e=para_decimal(
                    dados["emissao_kg_co2e"], campo="emissao_kg_co2e"
                ),
                unidade_ativa=(
                    True if unidade.get("ativa") is None else bool(unidade["ativa"])
                ),
            )
        )
    return lancamentos


def ultimo_snapshot(tenant_id: str, competencia: str):
    """O snapshot vigente da competencia: a maior versao gravada.

    Devolve (doc_id, dados) ou (None, None). Le so os snapshots daquele
    mes, que sao poucos -- nao a colecao inteira.
    """
    from google.cloud.firestore_v1.base_query import FieldFilter

    docs = list(
        colecao_do_tenant(tenant_id, COLECAO)
        .where(filter=FieldFilter("competencia", "==", competencia))
        .stream()
    )
    if not docs:
        return None, None

    ultimo = max(docs, key=lambda d: d.to_dict().get("versao", 0))
    return ultimo.id, ultimo.to_dict()


def gravar(
    tenant_id: str,
    agregado: Agregado,
    *,
    uid: str,
) -> tuple[str, dict, bool]:
    """Grava uma versao nova, ou devolve a existente se nada mudou.

    Retorna (id, documento, criado). `criado=False` significa reenvio
    sem mudanca: a resposta e 200 e nenhuma versao nasceu.
    """
    impressao = impressao_digital(agregado)
    id_anterior, anterior = ultimo_snapshot(tenant_id, agregado.competencia)

    if anterior is not None and anterior.get("impressao_digital") == impressao:
        return id_anterior, anterior, False

    versao = (anterior.get("versao", 0) + 1) if anterior else 1
    snapshot_id = id_do_snapshot(agregado.competencia, versao)

    documento = {
        "competencia": agregado.competencia,
        "versao": versao,
        "gerado_em": agora(),
        "gerado_por_uid": uid,
        "impressao_digital": impressao,
        "total_kg_co2e": como_texto(agregado.total_kg_co2e),
        "unidades_no_total": len(agregado.por_unidade),
        "por_regiao": [
            {
                "regiao": r.regiao,
                "emissao_kg_co2e": como_texto(r.emissao_kg_co2e),
                "unidades": r.unidades,
            }
            for r in agregado.por_regiao
        ],
        "por_escopo": [
            {"escopo": e.escopo, "emissao_kg_co2e": como_texto(e.emissao_kg_co2e)}
            for e in agregado.por_escopo
        ],
    }

    colecao = colecao_do_tenant(tenant_id, COLECAO)
    colecao.document(snapshot_id).set(documento)

    # As linhas por unidade vao em subcolecao, e nao dentro do documento:
    # e o que permite pagina-las (CA-07) sem carregar a rede inteira, e
    # mantem o documento do snapshot pequeno e barato de ler.
    linhas = colecao.document(snapshot_id).collection(SUBCOLECAO_UNIDADES)

    # Posicao gravada junto de cada linha: a ordem do ranking nao pode
    # depender de quem leu nem de como paginou. `por_unidade` ja vem
    # ordenada do dominio.
    for posicao, u in enumerate(agregado.por_unidade, start=1):
        linhas.document(u.unidade_id).set(
            {
                "unidade_id": u.unidade_id,
                "unidade_nome": u.unidade_nome,
                "regiao": u.regiao,
                "emissao_kg_co2e": como_texto(u.emissao_kg_co2e),
                "fontes_lancadas": u.fontes_lancadas,
                "unidade_ativa": u.unidade_ativa,
                "posicao": posicao,
            }
        )

    return snapshot_id, documento, True


def gerar(tenant_id: str, competencia: str, *, uid: str):
    """Le, agrega e grava. O caminho completo da geracao."""
    lancamentos = lancamentos_da_competencia(tenant_id, competencia)
    agregado = agregar(lancamentos, competencia)
    return gravar(tenant_id, agregado, uid=uid)


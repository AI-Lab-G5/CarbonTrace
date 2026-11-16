"""Snapshots e agregados prontos -- Jornada 4 (issue #35).

Divisao das rotas:

- POST /v1/snapshots            gera (a unica que grava)
- GET  /v1/snapshots            lista os snapshots, paginado
- GET  /v1/snapshots/{id}       um snapshot, com totais por regiao e escopo
- GET  /v1/snapshots/{id}/unidades   linhas por unidade, paginado
- GET  /v1/snapshots/{id}/comparacao ranking e desvio (CA-06)
- GET  /v1/agregados            atalho: o snapshot vigente da competencia

Nenhuma rota de leitura grava nada, nem gera snapshot sob demanda. Um
GET que gera torna o custo imprevisivel e faz duas telas abertas
disputarem o mesmo documento; alem disso o CA-03 exige em letra que
consulta nao dispare escrita.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth import Identidade, funcionario_atual
from app.db import colecao_do_tenant
from app.dominio.agregacao import TotalUnidade, comparar
from app.dominio.numeros import para_decimal
from app.models import (
    ComparacaoSaida,
    GeracaoSnapshot,
    LinhaComparacaoSaida,
    LinhaUnidade,
    Pagina,
    Snapshot,
    SnapshotGerado,
    SnapshotResumo,
)
from app.services.paginacao import fatiar
from app.services.snapshots import COLECAO, SUBCOLECAO_UNIDADES, gerar

router = APIRouter(prefix="/v1", tags=["agregados"])

# CA-07 fixa a paginacao das consultas de agregado em 20 por padrao e
# 100 no maximo -- mais apertado que o 50/200 das listas do CP2.
LIMITE_PADRAO = 20
LIMITE_MAXIMO = 100


def _resumo_de(doc_id: str, dados: dict) -> SnapshotResumo:
    return SnapshotResumo(
        id=doc_id,
        competencia=dados["competencia"],
        versao=dados["versao"],
        gerado_em=dados["gerado_em"],
        gerado_por_uid=dados["gerado_por_uid"],
        impressao_digital=dados["impressao_digital"],
        total_kg_co2e=para_decimal(dados["total_kg_co2e"], campo="total_kg_co2e"),
        unidades_no_total=dados["unidades_no_total"],
    )


def _snapshot_de(doc_id: str, dados: dict) -> Snapshot:
    return Snapshot(
        id=doc_id,
        competencia=dados["competencia"],
        versao=dados["versao"],
        gerado_em=dados["gerado_em"],
        gerado_por_uid=dados["gerado_por_uid"],
        impressao_digital=dados["impressao_digital"],
        total_kg_co2e=para_decimal(dados["total_kg_co2e"], campo="total_kg_co2e"),
        unidades_no_total=dados["unidades_no_total"],
        por_regiao=[
            {
                "regiao": r["regiao"],
                "emissao_kg_co2e": para_decimal(
                    r["emissao_kg_co2e"], campo="emissao_kg_co2e"
                ),
                "unidades": r["unidades"],
            }
            for r in dados.get("por_regiao", [])
        ],
        por_escopo=[
            {
                "escopo": e["escopo"],
                "emissao_kg_co2e": para_decimal(
                    e["emissao_kg_co2e"], campo="emissao_kg_co2e"
                ),
            }
            for e in dados.get("por_escopo", [])
        ],
    )


def _buscar(tenant_id: str, snapshot_id: str) -> dict:
    """Busca sob o caminho do tenant de quem chama.

    404 e nao 403 para empresa errada: distinguir os dois revelaria
    quais snapshots existem na outra empresa.
    """
    doc = colecao_do_tenant(tenant_id, COLECAO).document(snapshot_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Snapshot nao encontrado.")
    return doc.to_dict()


def _linha_de(dados: dict) -> LinhaUnidade:
    return LinhaUnidade(
        unidade_id=dados["unidade_id"],
        unidade_nome=dados["unidade_nome"],
        regiao=dados["regiao"],
        emissao_kg_co2e=para_decimal(
            dados["emissao_kg_co2e"], campo="emissao_kg_co2e"
        ),
        fontes_lancadas=dados["fontes_lancadas"],
        unidade_ativa=dados["unidade_ativa"],
        posicao=dados["posicao"],
    )


# --------------------------------------------------------------------
# Geracao -- a unica rota que grava
# --------------------------------------------------------------------


@router.post(
    "/snapshots",
    response_model=SnapshotGerado,
    summary="Gera o snapshot de uma competencia",
    description=(
        "201 quando nasce uma versao nova; 200 quando os lancamentos "
        "nao mudaram desde a ultima geracao -- nesse caso devolve o "
        "snapshot existente e `criado: false`, sem duplicar. Snapshot "
        "nunca e editado nem apagado: versoes anteriores ficam."
    ),
)
def gerar_snapshot(
    pedido: GeracaoSnapshot,
    resposta: Response,
    identidade: Identidade = Depends(funcionario_atual),
) -> SnapshotGerado:
    snapshot_id, dados, criado = gerar(
        identidade.tenant_id, pedido.competencia, uid=identidade.uid
    )
    resposta.status_code = (
        status.HTTP_201_CREATED if criado else status.HTTP_200_OK
    )
    return SnapshotGerado(criado=criado, snapshot=_snapshot_de(snapshot_id, dados))


# --------------------------------------------------------------------
# Leitura
# --------------------------------------------------------------------


@router.get("/snapshots", response_model=Pagina[SnapshotResumo])
def listar_snapshots(
    competencia: str | None = Query(default=None),
    limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
    cursor: str | None = Query(default=None),
    identidade: Identidade = Depends(funcionario_atual),
) -> Pagina[SnapshotResumo]:
    from google.cloud.firestore_v1.base_query import FieldFilter

    colecao = colecao_do_tenant(identidade.tenant_id, COLECAO)
    consulta = colecao
    if competencia:
        consulta = consulta.where(
            filter=FieldFilter("competencia", "==", competencia)
        )

    documentos, proximo = fatiar(colecao, consulta, cursor, limite)
    itens = [_resumo_de(d.id, d.to_dict()) for d in documentos]

    return Pagina(
        itens=itens,
        total_na_pagina=len(itens),
        limite=limite,
        proximo_cursor=proximo,
    )


@router.get("/snapshots/{snapshot_id}", response_model=Snapshot)
def obter_snapshot(
    snapshot_id: str,
    identidade: Identidade = Depends(funcionario_atual),
) -> Snapshot:
    return _snapshot_de(snapshot_id, _buscar(identidade.tenant_id, snapshot_id))


@router.get(
    "/snapshots/{snapshot_id}/unidades",
    response_model=Pagina[LinhaUnidade],
    summary="Linhas por unidade de um snapshot",
    description=(
        "Paginado por cursor. O total do snapshot nao depende da pagina: "
        "ele ja esta em GET /v1/snapshots/{snapshot_id}."
    ),
)
def listar_unidades(
    snapshot_id: str,
    regiao: str | None = Query(default=None, description="Filtra por UF"),
    limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
    cursor: str | None = Query(default=None),
    identidade: Identidade = Depends(funcionario_atual),
) -> Pagina[LinhaUnidade]:
    from google.cloud.firestore_v1.base_query import FieldFilter

    _buscar(identidade.tenant_id, snapshot_id)

    colecao = (
        colecao_do_tenant(identidade.tenant_id, COLECAO)
        .document(snapshot_id)
        .collection(SUBCOLECAO_UNIDADES)
    )
    consulta = colecao
    regiao_limpa = regiao.strip().upper() if regiao else ""
    if regiao_limpa:
        consulta = consulta.where(filter=FieldFilter("regiao", "==", regiao_limpa))

    documentos, proximo = fatiar(colecao, consulta, cursor, limite)
    itens = [_linha_de(d.to_dict()) for d in documentos]

    return Pagina(
        itens=itens,
        total_na_pagina=len(itens),
        limite=limite,
        proximo_cursor=proximo,
    )


@router.get(
    "/snapshots/{snapshot_id}/comparacao",
    response_model=ComparacaoSaida,
    summary="Ranking e desvio contra a mediana (CA-06)",
    description=(
        "Elegivel: unidade ativa com pelo menos uma fonte lancada. "
        "Alerta so quando o desvio absoluto passa de 50%, com no minimo "
        "3 elegiveis e mediana positiva; exatamente +/-50% nao alerta. "
        "Fora disso, `disponivel: false` com o motivo."
    ),
)
def obter_comparacao(
    snapshot_id: str,
    identidade: Identidade = Depends(funcionario_atual),
) -> ComparacaoSaida:
    dados = _buscar(identidade.tenant_id, snapshot_id)

    linhas = (
        colecao_do_tenant(identidade.tenant_id, COLECAO)
        .document(snapshot_id)
        .collection(SUBCOLECAO_UNIDADES)
        .stream()
    )

    # Elegibilidade: ativa e com coleta no mes. A terceira condicao do
    # CA-06 -- "tem fonte esperada" -- precisa de um campo de fonte
    # esperada por unidade, que o cadastro ainda nao tem (#34). Esta
    # limitacao esta registrada no ADR-010 para nao passar por pronta.
    elegiveis = []
    for doc in linhas:
        d = doc.to_dict()
        if d["unidade_ativa"] and d["fontes_lancadas"] > 0:
            elegiveis.append(
                TotalUnidade(
                    unidade_id=d["unidade_id"],
                    unidade_nome=d["unidade_nome"],
                    regiao=d["regiao"],
                    emissao_kg_co2e=para_decimal(
                        d["emissao_kg_co2e"], campo="emissao_kg_co2e"
                    ),
                    fontes_lancadas=d["fontes_lancadas"],
                    unidade_ativa=True,
                )
            )

    comparacao = comparar(elegiveis)

    return ComparacaoSaida(
        competencia=dados["competencia"],
        snapshot_id=snapshot_id,
        disponivel=comparacao.disponivel,
        motivo=comparacao.motivo,
        mediana_kg_co2e=comparacao.mediana_kg_co2e,
        elegiveis=len(elegiveis),
        linhas=[
            LinhaComparacaoSaida(
                unidade_id=linha.unidade_id,
                unidade_nome=linha.unidade_nome,
                emissao_kg_co2e=linha.emissao_kg_co2e,
                desvio_percentual=linha.desvio_percentual,
                alerta=linha.alerta,
            )
            for linha in comparacao.linhas
        ],
    )


@router.get(
    "/agregados",
    response_model=Snapshot,
    summary="O snapshot vigente de uma competencia",
    description=(
        "Atalho para o dashboard: devolve a maior versao gravada da "
        "competencia, sem precisar listar antes. 404 quando a "
        "competencia ainda nao teve snapshot gerado -- a leitura nunca "
        "gera um por conta propria."
    ),
)
def obter_agregado_vigente(
    competencia: str = Query(description="Mes de referencia, formato AAAA-MM"),
    identidade: Identidade = Depends(funcionario_atual),
) -> Snapshot:
    from app.services.snapshots import ultimo_snapshot

    snapshot_id, dados = ultimo_snapshot(identidade.tenant_id, competencia)
    if dados is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nenhum snapshot gerado para {competencia}. "
                "Gere com POST /v1/snapshots."
            ),
        )
    return _snapshot_de(snapshot_id, dados)

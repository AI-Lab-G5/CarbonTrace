"""Leitura do catalogo de fatores versionados.

Fatores sao globais e imutaveis: uma versao publicada nunca e editada.
Corrigir um numero significa publicar uma versao nova. Sem isso, um
relatorio emitido em marco deixaria de bater consigo mesmo em dezembro.

Nao ha tela nem rota de publicacao: versao nova entra pelo seed, que e
operacao administrativa. O CA-01 dispensa isso de proposito.
"""

from decimal import Decimal
from functools import lru_cache

from app.db import colecao_global
from app.dominio.calculo import FatorAplicado
from app.dominio.erros import FatorNaoEncontrado
from app.dominio.numeros import para_decimal
from app.models import Fator, VersaoFatores


def _fator_do_documento(bruto: dict) -> Fator:
    """Converte o documento do Firestore no modelo, com Decimal.

    Os numeros estao gravados como texto justamente para chegarem aqui
    sem passar por float em nenhum ponto do caminho.
    """
    return Fator(
        fonte_id=bruto["fonte_id"],
        nome=bruto["nome"],
        escopo=bruto["escopo"],
        unidade_base=bruto["unidade_base"],
        unidades_aceitas=bruto["unidades_aceitas"],
        kg_co2e_por_unidade=para_decimal(
            bruto["kg_co2e_por_unidade"], campo="kg_co2e_por_unidade"
        ),
        teto_mensal=para_decimal(bruto["teto_mensal"], campo="teto_mensal"),
        fonte_referencia=bruto["fonte_referencia"],
        status=bruto["status"],
    )


@lru_cache(maxsize=16)
def carregar_versao(versao: str) -> VersaoFatores | None:
    """Le uma versao do Firestore.

    O cache e seguro porque a versao e imutavel: o conteudo de 'v1' hoje
    e o mesmo de daqui a um ano.
    """
    doc = colecao_global("fatores").document(versao).get()
    if not doc.exists:
        return None

    dados = doc.to_dict()
    return VersaoFatores(
        versao=versao,
        vigencia_inicio=dados["vigencia_inicio"],
        vigencia_fim=dados.get("vigencia_fim"),
        publicado_em=dados["publicado_em"],
        status=dados["status"],
        fatores=[_fator_do_documento(f) for f in dados["fatores"]],
    )


def listar_versoes() -> list[str]:
    return sorted(d.id for d in colecao_global("fatores").stream())


def versao_vigente(competencia: str) -> str:
    """Versao de fatores que vale para uma competencia.

    A mais recente cuja vigencia comecou ate a competencia informada.
    Um lancamento de 2025-03 usa os fatores de 2025, mesmo digitado
    em 2026 -- e e isso que torna o recalculo reproduzivel.
    """
    candidatas: list[tuple[str, str]] = []
    for doc in colecao_global("fatores").stream():
        dados = doc.to_dict()
        inicio = dados.get("vigencia_inicio", "")
        fim = dados.get("vigencia_fim")
        if inicio <= competencia and (fim is None or competencia <= fim):
            candidatas.append((inicio, doc.id))

    if not candidatas:
        raise FatorNaoEncontrado(fonte_id="*", competencia=competencia)

    return max(candidatas)[1]


def buscar_fator(versao: str, fonte_id: str) -> Fator | None:
    conjunto = carregar_versao(versao)
    if conjunto is None:
        return None
    return next((f for f in conjunto.fatores if f.fonte_id == fonte_id), None)


def fator_para(fonte_id: str, competencia: str) -> FatorAplicado:
    """Resolve o fator aplicavel e devolve a forma que o dominio usa.

    Levanta FatorNaoEncontrado quando a fonte nao existe na versao
    vigente -- o caso do CA-04 de fator ausente.
    """
    versao = versao_vigente(competencia)
    fator = buscar_fator(versao, fonte_id)

    if fator is None:
        raise FatorNaoEncontrado(fonte_id=fonte_id, competencia=competencia)

    return FatorAplicado(
        fonte_id=fator.fonte_id,
        versao=versao,
        valor=fator.kg_co2e_por_unidade,
        unidade_base=fator.unidade_base,
        escopo=fator.escopo,
        teto=fator.teto_mensal,
    )


def fator_da_versao(fonte_id: str, versao: str) -> FatorAplicado:
    """Recupera um fator por versao explicita, para recalculo.

    E o caminho da prova do CA-03: dado o que o lancamento guardou,
    refazer a conta com o fator original.
    """
    fator = buscar_fator(versao, fonte_id)
    if fator is None:
        raise FatorNaoEncontrado(fonte_id=fonte_id, competencia=f"versao {versao}")

    return FatorAplicado(
        fonte_id=fator.fonte_id,
        versao=versao,
        valor=fator.kg_co2e_por_unidade,
        unidade_base=fator.unidade_base,
        escopo=fator.escopo,
        teto=fator.teto_mensal,
    )


def emissao_como_decimal(valor: object) -> Decimal:
    """Le de volta um numero gravado como texto no Firestore."""
    return para_decimal(valor, campo="emissao_kg_co2e")

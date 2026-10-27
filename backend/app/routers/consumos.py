"""Lancamentos mensais de consumo e seus resultados calculados.

Jornadas 2 e 3: registrar consumo validado e calcular a emissao com o
fator versionado da competencia.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import Identidade, funcionario_atual
from app.db import colecao_do_tenant
from app.dominio.calculo import calcular, recalcular
from app.dominio.erros import ErroDeDominio
from app.models import Consumo, ConsumoEntrada, Pagina
from app.services.fatores import fator_da_versao, fator_para
from app.services.paginacao import LIMITE_MAXIMO, LIMITE_PADRAO, fatiar
from app.services.persistencia import (
    consumo_de_documento,
    documento_de_consumo,
    resultado_de_consumo,
)

router = APIRouter(prefix="/v1/consumos", tags=["consumos"])


def _chave_natural(entrada: ConsumoEntrada) -> str:
    """Identificador deterministico de um lancamento.

    Uma unidade so tem um lancamento por fonte por competencia. Derivar
    o id dessa chave faz o reenvio do mesmo pedido sobrescrever em vez de
    duplicar -- idempotencia sem tabela de controle. Ver ADR-006.
    """
    return f"{entrada.unidade_id}_{entrada.competencia}_{entrada.fonte_id}"


def _erro_422(erro: ErroDeDominio) -> HTTPException:
    return HTTPException(
         status_code=422,
        detail=erro.mensagem(),
    )


@router.get("", response_model=Pagina[Consumo])
def listar(
    competencia: str | None = Query(default=None),
    unidade_id: str | None = Query(default=None),
    limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
    cursor: str | None = Query(default=None, description="proximo_cursor da pagina anterior"),
    identidade: Identidade = Depends(funcionario_atual),
) -> Pagina[Consumo]:
    from google.cloud.firestore_v1.base_query import FieldFilter

    colecao = colecao_do_tenant(identidade.tenant_id, "consumos")
    consulta = colecao
    if competencia:
        consulta = consulta.where(filter=FieldFilter("competencia", "==", competencia))
    if unidade_id:
        consulta = consulta.where(filter=FieldFilter("unidade_id", "==", unidade_id))

    documentos, proximo = fatiar(colecao, consulta, cursor, limite)
    itens = [consumo_de_documento(d.id, d.to_dict()) for d in documentos]

    return Pagina(
        itens=itens,
        total_na_pagina=len(itens),
        limite=limite,
        proximo_cursor=proximo,
    )


@router.get("/{consumo_id}", response_model=Consumo)
def obter(
    consumo_id: str,
    identidade: Identidade = Depends(funcionario_atual),
) -> Consumo:
    doc = colecao_do_tenant(identidade.tenant_id, "consumos").document(consumo_id).get()
    if not doc.exists:
        # 404 e nao 403: quem pergunta por um lancamento de outra empresa
        # recebe a mesma resposta de quem pergunta por um inexistente.
        # Distinguir os dois casos revelaria quais ids existem por ai.
        raise HTTPException(status_code=404, detail="Consumo nao encontrado.")
    return consumo_de_documento(doc.id, doc.to_dict())


@router.put("", response_model=Consumo)
def registrar(
    entrada: ConsumoEntrada,
    identidade: Identidade = Depends(funcionario_atual),
) -> Consumo:
    """Grava ou atualiza um lancamento, ja calculado.

    PUT e nao POST porque a operacao e idempotente: o mesmo pedido
    repetido leva ao mesmo estado, sem lancamento duplicado.
    """
    unidade = (
        colecao_do_tenant(identidade.tenant_id, "unidades")
        .document(entrada.unidade_id)
        .get()
    )
    if not unidade.exists:
        raise HTTPException(status_code=404, detail="Unidade nao encontrada.")

    try:
        fator = fator_para(entrada.fonte_id, entrada.competencia)
        resultado = calcular(entrada.quantidade, entrada.unidade_medida, fator)
    except ErroDeDominio as erro:
        raise _erro_422(erro) from erro

    doc_id = _chave_natural(entrada)
    dados = documento_de_consumo(entrada, resultado)
    colecao_do_tenant(identidade.tenant_id, "consumos").document(doc_id).set(dados)

    return consumo_de_documento(doc_id, dados)


@router.post("/{consumo_id}/recalculo", response_model=Consumo)
def conferir_recalculo(
    consumo_id: str,
    identidade: Identidade = Depends(funcionario_atual),
) -> Consumo:
    """Refaz a conta com o fator original e confere contra o gravado.

    Prova do CA-03, disponivel para auditoria: mesmo que uma versao nova
    de fatores tenha sido publicada, este endpoint usa a versao que o
    lancamento registrou. O valor tem de bater com o guardado -- se
    divergir, ha defeito no motor de calculo, e 500 e a resposta certa
    porque o erro e nosso, nao de quem chamou.
    """
    doc = colecao_do_tenant(identidade.tenant_id, "consumos").document(consumo_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Consumo nao encontrado.")

    gravado = consumo_de_documento(doc.id, doc.to_dict())

    try:
        fator = fator_da_versao(gravado.fonte_id, gravado.fator_versao)
        refeito = recalcular(resultado_de_consumo(gravado), fator)
    except ErroDeDominio as erro:
        raise _erro_422(erro) from erro

    if refeito.emissao_kg_co2e != gravado.emissao_kg_co2e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Recalculo divergiu do valor gravado: {refeito.emissao_kg_co2e} "
                f"contra {gravado.emissao_kg_co2e}."
            ),
        )

    return gravado

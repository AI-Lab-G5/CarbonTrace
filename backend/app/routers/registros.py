"""Lancamentos mensais de consumo por unidade."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import Identidade, exige_escrita, identidade_atual
from app.db import colecao_do_tenant
from app.models import Registro, RegistroEntrada
from app.services.calculo import calcular_emissao
from app.services.fatores import buscar_fator, versao_vigente

router = APIRouter(prefix="/v1/registros", tags=["registros"])


def _chave_natural(entrada: RegistroEntrada) -> str:
    """Identificador deterministico de um lancamento.

    Uma unidade so pode ter um lancamento por fonte por competencia.
    Derivar o id do documento desses tres campos faz o reenvio do mesmo
    POST sobrescrever o registro em vez de criar um duplicado -- ou seja,
    a operacao e idempotente sem precisar de tabela de controle.
    """
    return f"{entrada.unidade_id}_{entrada.competencia}_{entrada.fonte_id}"


@router.get("", response_model=list[Registro])
def listar(
    competencia: str | None = Query(default=None),
    unidade_id: str | None = Query(default=None),
    identidade: Identidade = Depends(identidade_atual),
) -> list[Registro]:
    consulta = colecao_do_tenant(identidade.tenant_id, "registros")
    if competencia:
        consulta = consulta.where("competencia", "==", competencia)
    if unidade_id:
        consulta = consulta.where("unidade_id", "==", unidade_id)
    return [Registro(id=d.id, **d.to_dict()) for d in consulta.stream()]


@router.put("", response_model=Registro)
def registrar(
    entrada: RegistroEntrada,
    identidade: Identidade = Depends(exige_escrita),
) -> Registro:
    """Grava ou atualiza um lancamento.

    PUT, e nao POST, justamente porque a operacao e idempotente: o mesmo
    pedido repetido leva ao mesmo estado, sem efeito colateral extra.
    """
    unidade = (
        colecao_do_tenant(identidade.tenant_id, "unidades")
        .document(entrada.unidade_id)
        .get()
    )
    if not unidade.exists:
        raise HTTPException(status_code=404, detail="Unidade nao encontrada.")

    versao = versao_vigente(entrada.competencia)
    fator = buscar_fator(versao, entrada.fonte_id)
    if fator is None:
        raise HTTPException(
            status_code=422,
            detail=f"Fonte '{entrada.fonte_id}' nao existe na versao {versao} dos fatores.",
        )

    dados = {
        "unidade_id": entrada.unidade_id,
        "competencia": entrada.competencia,
        "fonte_id": entrada.fonte_id,
        "quantidade": entrada.quantidade,
        "unidade_medida": fator.unidade_medida,
        # A versao do fator fica gravada junto do lancamento. E isso que
        # permite recalcular o passado com o fator da epoca, mesmo depois
        # de publicarmos uma versao nova.
        "fator_versao": versao,
        "fator_valor": fator.kg_co2e_por_unidade,
        "emissao_kg_co2e": calcular_emissao(entrada.quantidade, fator),
        "escopo": fator.escopo,
    }

    doc_id = _chave_natural(entrada)
    colecao_do_tenant(identidade.tenant_id, "registros").document(doc_id).set(dados)
    return Registro(id=doc_id, **dados)

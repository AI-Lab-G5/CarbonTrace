"""Unidades da rede: lojas, filiais e franquias. Jornada 1."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import Identidade, funcionario_atual
from app.db import colecao_do_tenant
from app.models import Pagina, Unidade
from app.services.paginacao import LIMITE_MAXIMO, LIMITE_PADRAO, fatiar

router = APIRouter(prefix="/v1/unidades", tags=["unidades"])


@router.get("", response_model=Pagina[Unidade])
def listar(
    limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
    cursor: str | None = Query(default=None, description="proximo_cursor da pagina anterior"),
    identidade: Identidade = Depends(funcionario_atual),
) -> Pagina[Unidade]:
    colecao = colecao_do_tenant(identidade.tenant_id, "unidades")
    documentos, proximo = fatiar(colecao, colecao, cursor, limite)

    return Pagina(
        itens=[Unidade(id=d.id, **d.to_dict()) for d in documentos],
        total_na_pagina=len(documentos),
        limite=limite,
        proximo_cursor=proximo,
    )


@router.get("/{unidade_id}", response_model=Unidade)
def obter(
    unidade_id: str,
    identidade: Identidade = Depends(funcionario_atual),
) -> Unidade:
    doc = colecao_do_tenant(identidade.tenant_id, "unidades").document(unidade_id).get()
    if not doc.exists:
        # 404 e nao 403 de proposito: ver nota em consumos.py.
        raise HTTPException(status_code=404, detail="Unidade nao encontrada.")
    return Unidade(id=doc.id, **doc.to_dict())


@router.post("", response_model=Unidade, status_code=201)
def criar(
    entrada: Unidade,
    identidade: Identidade = Depends(funcionario_atual),
) -> Unidade:
    dados = entrada.model_dump(exclude={"id"})
    ref = colecao_do_tenant(identidade.tenant_id, "unidades").document()
    ref.set(dados)
    return Unidade(id=ref.id, **dados)

"""Unidades da rede (lojas, filiais, franquias)."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import Identidade, exige_escrita, identidade_atual
from app.db import colecao_do_tenant
from app.models import Unidade

router = APIRouter(prefix="/v1/unidades", tags=["unidades"])


@router.get("", response_model=list[Unidade])
def listar(identidade: Identidade = Depends(identidade_atual)) -> list[Unidade]:
    docs = colecao_do_tenant(identidade.tenant_id, "unidades").stream()
    return [Unidade(id=d.id, **d.to_dict()) for d in docs]


@router.get("/{unidade_id}", response_model=Unidade)
def obter(unidade_id: str, identidade: Identidade = Depends(identidade_atual)) -> Unidade:
    doc = colecao_do_tenant(identidade.tenant_id, "unidades").document(unidade_id).get()
    if not doc.exists:
        # 404 e nao 403: quem pergunta por uma unidade de outra empresa
        # recebe a mesma resposta de quem pergunta por uma que nao existe.
        # Distinguir os dois casos vazaria quais ids existem por ai.
        raise HTTPException(status_code=404, detail="Unidade nao encontrada.")
    return Unidade(id=doc.id, **doc.to_dict())


@router.post("", response_model=Unidade, status_code=201)
def criar(entrada: Unidade, identidade: Identidade = Depends(exige_escrita)) -> Unidade:
    dados = entrada.model_dump(exclude={"id"})
    ref = colecao_do_tenant(identidade.tenant_id, "unidades").document()
    ref.set(dados)
    return Unidade(id=ref.id, **dados)

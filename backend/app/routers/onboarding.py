"""Onboarding aceita identidade sem empresa; negócios continuam protegidos."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.auth import Identidade, claims_do_token, funcionario_atual
from app.services.convites import resgatar

router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


class Resgate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    convite: str = Field(min_length=32, max_length=256)


@router.post("/resgate")
def resgate(body: Resgate, claims: dict = Depends(claims_do_token)):
    return resgatar(body.convite, claims)


@router.get("/acesso")
def acesso(pessoa: Identidade = Depends(funcionario_atual)):
    return {"tenant_id": pessoa.tenant_id, "papel": pessoa.papel}

"""Consulta aos fatores de emissao versionados. Somente leitura."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import Identidade, identidade_atual
from app.models import VersaoFatores
from app.services.fatores import carregar_versao, listar_versoes

router = APIRouter(prefix="/v1/fatores", tags=["fatores"])


@router.get("/versoes", response_model=list[str])
def versoes(_: Identidade = Depends(identidade_atual)) -> list[str]:
    return listar_versoes()


@router.get("/{versao}", response_model=VersaoFatores)
def obter(versao: str, _: Identidade = Depends(identidade_atual)) -> VersaoFatores:
    conjunto = carregar_versao(versao)
    if conjunto is None:
        raise HTTPException(status_code=404, detail="Versao de fatores nao encontrada.")
    return conjunto

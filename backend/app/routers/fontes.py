"""Catalogo de fontes de emissao aprovadas. Jornada 1.

Somente leitura: as quatro fontes e seus fatores sao definidos pelo
catalogo versionado, nao pela empresa cliente. Nao ha tela nem rota de
publicacao -- CA-01 dispensa.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import Identidade, funcionario_atual
from app.dominio.competencia import hoje_competencia
from app.models import Fator, VersaoFatores
from app.services.fatores import carregar_versao, listar_versoes, versao_vigente

router = APIRouter(prefix="/v1/fontes", tags=["fontes"])


@router.get("", response_model=list[Fator])
def listar(
    competencia: str | None = None,
    _: Identidade = Depends(funcionario_atual),
) -> list[Fator]:
    """Fontes vigentes na competencia pedida, ou no mes corrente.

    O front usa esta rota para montar o seletor de fonte e saber quais
    unidades de medida aceitar em cada uma.
    """
    alvo = competencia or hoje_competencia()
    conjunto = carregar_versao(versao_vigente(alvo))
    if conjunto is None:
        raise HTTPException(status_code=404, detail="Nenhum catalogo publicado.")
    return conjunto.fatores


@router.get("/versoes", response_model=list[str])
def versoes(_: Identidade = Depends(funcionario_atual)) -> list[str]:
    return listar_versoes()


@router.get("/versoes/{versao}", response_model=VersaoFatores)
def obter_versao(
    versao: str,
    _: Identidade = Depends(funcionario_atual),
) -> VersaoFatores:
    conjunto = carregar_versao(versao)
    if conjunto is None:
        raise HTTPException(status_code=404, detail="Versao de fatores nao encontrada.")
    return conjunto

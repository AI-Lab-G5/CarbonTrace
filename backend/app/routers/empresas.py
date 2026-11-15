"""Cadastro de empresas -- CA-01 da issue #35.

Quem pode criar
---------------
Uma conta autenticada que ainda nao pertence a empresa nenhuma. E o
fluxo de quem esta abrindo a propria empresa no sistema.

Quem ja esta vinculado recebe 403: sem isso, qualquer funcionario de
qualquer empresa poderia criar empresas a vontade, e essa seria uma
porta aberta que o CP3 nao pediu. Nao ha papel administrativo no
sistema -- o unico papel e `funcionario` -- entao esta e a restricao
mais apertada que da para aplicar hoje sem inventar um papel que o Tech
Lead ainda nao definiu (#34).

Criar a empresa nao vincula ninguem a ela: o vinculo continua sendo
feito por convite (`POST /v1/onboarding/resgate`), que e onde as custom
claims sao atribuidas. Juntar as duas coisas numa chamada so e trabalho
para quando o fluxo de cadastro estiver definido.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import claims_do_token
from app.models import Empresa, EmpresaEntrada
from app.services.empresas import buscar, criar

router = APIRouter(prefix="/v1/empresas", tags=["empresas"])


@router.post(
    "",
    response_model=Empresa,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Codigo ja usado por outra empresa"}},
    summary="Cadastra uma empresa com codigo unico",
)
def cadastrar(
    entrada: EmpresaEntrada,
    claims: dict = Depends(claims_do_token),
) -> Empresa:
    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Identidade invalida.")

    if claims.get("tenant_id"):
        raise HTTPException(
            status_code=403,
            detail=(
                "Esta conta ja pertence a uma empresa. Para abrir outra, "
                "fale com a equipe."
            ),
        )

    return Empresa(**criar(entrada.codigo, entrada.nome, uid=uid))


@router.get(
    "/{codigo}",
    response_model=Empresa,
    summary="Consulta uma empresa pelo codigo",
    description=(
        "Publico para quem esta autenticado: serve para a tela de "
        "cadastro dizer se um codigo esta livre antes de enviar. Devolve "
        "apenas codigo e nome -- nenhum dado de consumo."
    ),
)
def obter(codigo: str, claims: dict = Depends(claims_do_token)) -> Empresa:
    dados = buscar(codigo)
    if dados is None:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada.")
    return Empresa(**dados)

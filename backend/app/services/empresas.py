"""Cadastro de empresas com codigo unico -- CA-01 da issue #35.

A unicidade nao e conferida com "busca antes de gravar": entre a busca e
a gravacao cabe outra requisicao com o mesmo codigo, e as duas passam.
Quem garante e o proprio Firestore, pelo `create()`, que falha se o
documento ja existe -- o codigo e o id do documento, e id duplicado nao
existe. A condicao de corrida deixa de ser possivel em vez de ficar
improvavel.
"""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from google.api_core import exceptions as google_exceptions

from app.db import colecao_global
from app.services.autoria import marcar_criacao

COLECAO = "empresas"

# Minusculas, digitos e hifen. Sem barra, que quebraria o caminho do
# documento, e sem maiuscula, para que "ACME" e "acme" nao virem duas
# empresas diferentes que ninguem distingue na tela.
PADRAO_CODIGO = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$")

CODIGO_INVALIDO = (
    "Codigo deve ter de 3 a 40 caracteres, apenas minusculas, digitos e "
    "hifen, comecando e terminando com letra ou digito."
)


def normalizar(codigo: str) -> str:
    """Minusculas e sem espaco nas pontas, antes de validar."""
    return codigo.strip().casefold()


def validar_codigo(codigo: str) -> str:
    normalizado = normalizar(codigo)
    if not PADRAO_CODIGO.match(normalizado):
        raise ValueError(CODIGO_INVALIDO)
    return normalizado


def criar(codigo: str, nome: str, *, uid: str) -> dict:
    """Cria a empresa. 409 se o codigo ja existe."""
    codigo = validar_codigo(codigo)

    documento = marcar_criacao({"codigo": codigo, "nome": nome.strip()}, uid)

    try:
        colecao_global(COLECAO).document(codigo).create(documento)
    except google_exceptions.AlreadyExists as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ja existe uma empresa com o codigo '{codigo}'.",
        ) from erro

    return documento


def buscar(codigo: str) -> dict | None:
    doc = colecao_global(COLECAO).document(normalizar(codigo)).get()
    return doc.to_dict() if doc.exists else None

"""Identidade do chamador e escopo de empresa.

Toda rota protegida depende de `funcionario_atual`. O tenant vem das
custom claims do ID token, assinadas pelo Firebase -- nunca de parametro
enviado pelo cliente. E esse valor que monta o caminho das consultas.

A verificacao do token e uma dependencia separada (`claims_do_token`) de
proposito: os testes a substituem para exercitar token ausente, expirado,
papel errado e empresa errada de forma deterministica, sem depender de
emitir tokens reais. A verificacao em si e codigo do Firebase; o que
precisamos provar e a nossa autorizacao.
"""

from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

Papel = Literal["funcionario"]

PAPEIS_VALIDOS: frozenset[str] = frozenset({"funcionario"})

esquema_bearer = HTTPBearer(auto_error=False, description="ID token do Firebase")


@dataclass(frozen=True)
class Identidade:
    uid: str
    tenant_id: str
    papel: Papel
    email: str | None = None


def _nao_autenticado(detalhe: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalhe,
        headers={"WWW-Authenticate": "Bearer"},
    )


def claims_do_token(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> dict:
    """Verifica o ID token e devolve as claims.

    Com FIREBASE_AUTH_EMULATOR_HOST definido, o SDK do Firebase aceita os
    tokens do emulador sem conferir assinatura -- e por isso que o
    ambiente local nao precisa de credencial de producao.
    """
    if credenciais is None or not credenciais.credentials:
        raise _nao_autenticado("Authorization: Bearer <id_token> e obrigatorio.")

    # Import local: so e necessario quando ha token para verificar, o que
    # mantem os testes de dominio livres da dependencia.
    import firebase_admin
    from firebase_admin import auth as fb_auth

    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    try:
        return fb_auth.verify_id_token(credenciais.credentials)
    except fb_auth.ExpiredIdTokenError as erro:
        raise _nao_autenticado("Token expirado. Entre novamente.") from erro
    except fb_auth.RevokedIdTokenError as erro:
        raise _nao_autenticado("Token revogado. Entre novamente.") from erro
    except Exception as erro:  # noqa: BLE001 - o SDK lanca varios tipos
        raise _nao_autenticado("Token invalido.") from erro


def identidade_atual(claims: dict = Depends(claims_do_token)) -> Identidade:
    """Monta a identidade a partir das claims verificadas."""
    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem empresa associada. Procure o administrador.",
        )

    papel = claims.get("papel")
    if papel not in PAPEIS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Papel sem permissao para esta operacao.",
        )

    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise _nao_autenticado("Token sem identificacao de usuario.")

    return Identidade(
        uid=uid,
        tenant_id=tenant_id,
        papel=papel,  # type: ignore[arg-type]
        email=claims.get("email"),
    )


def funcionario_atual(
    identidade: Identidade = Depends(identidade_atual),
) -> Identidade:
    """Dependencia padrao das rotas de negocio.

    Hoje `identidade_atual` ja garante o papel, mas a indirecao deixa o
    ponto de extensao pronto para quando houver mais de um perfil --
    sem mexer em todas as rotas de novo.
    """
    return identidade

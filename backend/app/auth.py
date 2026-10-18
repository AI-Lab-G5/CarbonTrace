"""Identidade do chamador e escopo de tenant.

Toda rota protegida depende de `identidade_atual`. Ela devolve o tenant
do usuario, e e esse valor -- nunca um parametro vindo do cliente -- que
monta o caminho das consultas no Firestore. O cliente nao escolhe em qual
empresa quer ler.
"""

from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException, status

from app.config import settings

Papel = Literal["leitor", "operador", "gestor"]


@dataclass(frozen=True)
class Identidade:
    uid: str
    tenant_id: str
    papel: Papel


def _identidade_do_emulador(
    x_debug_uid: str | None,
    x_debug_tenant: str | None,
    x_debug_papel: str | None,
) -> Identidade:
    """Identidade falsa para desenvolvimento local.

    So existe quando AUTH_MODE=emulator. Confiar em um cabecalho enviado
    pelo cliente seria uma falha grave em producao -- por isso o modo e
    lido do ambiente do servidor, e nunca do pedido.
    """
    if not x_debug_uid or not x_debug_tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Em AUTH_MODE=emulator envie X-Debug-Uid e X-Debug-Tenant.",
        )
    papel = x_debug_papel or "gestor"
    if papel not in ("leitor", "operador", "gestor"):
        raise HTTPException(status_code=400, detail="Papel invalido.")
    return Identidade(uid=x_debug_uid, tenant_id=x_debug_tenant, papel=papel)  # type: ignore[arg-type]


def _identidade_do_firebase(authorization: str | None) -> Identidade:
    """Identidade real, extraida de um ID token do Firebase Auth.

    O tenant e o papel vem de custom claims, gravadas no token quando o
    usuario e convidado para uma empresa. Claims sao assinadas pelo
    Firebase, entao o cliente nao consegue forjar as suas.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer <id_token> e obrigatorio.",
        )

    token = authorization.removeprefix("Bearer ").strip()

    # Import local: firebase_admin so e necessario fora do modo emulador.
    import firebase_admin
    from firebase_admin import auth as fb_auth

    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    try:
        claims = fb_auth.verify_id_token(token)
    except Exception as erro:  # noqa: BLE001 - a lib lanca varios tipos
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado.",
        ) from erro

    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem empresa associada.",
        )

    return Identidade(
        uid=claims["uid"],
        tenant_id=tenant_id,
        papel=claims.get("papel", "leitor"),
    )


def identidade_atual(
    authorization: str | None = Header(default=None),
    x_debug_uid: str | None = Header(default=None),
    x_debug_tenant: str | None = Header(default=None),
    x_debug_papel: str | None = Header(default=None),
) -> Identidade:
    if settings.auth_mode == "emulator":
        return _identidade_do_emulador(x_debug_uid, x_debug_tenant, x_debug_papel)
    return _identidade_do_firebase(authorization)


def exige_escrita(identidade: Identidade = Depends(identidade_atual)) -> Identidade:
    """Barra quem so tem permissao de leitura."""
    if identidade.papel == "leitor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Papel 'leitor' nao pode gravar.",
        )
    return identidade

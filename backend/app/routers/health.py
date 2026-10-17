"""Health check. Rota publica, sem autenticacao."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["infra"])


@router.get("/health")
def health() -> dict:
    """Prova de vida da API.

    Usado pelo healthcheck do Docker Compose e pelo teste de fumaca do CI.
    Nao toca no Firestore de proposito: se o banco cair, o container ainda
    responde e o log mostra onde esta o problema.
    """
    return {
        "status": "ok",
        "servico": "carbontrace-api",
        "modo_auth": settings.auth_mode,
        "emulador": settings.usando_emulador,
    }

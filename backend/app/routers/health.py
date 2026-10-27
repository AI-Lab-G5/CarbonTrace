"""Sondas de saude. Rotas publicas, as unicas sem autenticacao.

Separadas de proposito, conforme o guia do checkpoint:

  /healthz  -- o processo esta de pe? Nao toca em dependencia nenhuma.
  /readyz   -- da para atender pedido? Confere o Firestore.

A distincao importa em producao: um /healthz que consulta o banco faz o
orquestrador reiniciar a aplicacao quando quem caiu foi o banco, e o
reinicio nao conserta nada.
"""

from fastapi import APIRouter, Response, status

from app.config import settings

router = APIRouter(tags=["infra"])


@router.get(
    "/healthz",
    summary="Prova de vida do processo",
    description=(
        "**Rota publica, sem autenticacao.** Excecao acordada com o Tech "
        "Lead e registrada no CA-02: a sonda de liveness e chamada pelo "
        "orquestrador, que nao tem token, e precisa responder mesmo "
        "quando o Firebase Auth esta fora do ar -- se exigisse token, "
        "uma falha de autenticacao derrubaria a aplicacao inteira. Nao "
        "expoe nenhum dado de cliente."
    ),
)
def healthz() -> dict:
    return {
        "status": "ok",
        "servico": "carbontrace-api",
        "emulador": settings.usando_emulador,
    }


@router.get(
    "/readyz",
    summary="Prontidao para atender",
    description=(
        "**Rota publica, sem autenticacao.** Mesma excecao do /healthz. "
        "Responde 200 quando o Firestore responde e 503 quando nao. A "
        "mensagem de erro do 503 nao inclui dado de cliente."
    ),
)
def readyz(resposta: Response) -> dict:
    """Confere se o Firestore responde.

    Devolve 503 quando nao responde, para o balanceador tirar esta
    instancia da rotacao sem derrubar o processo.
    """
    from app.db import get_db

    try:
        # Leitura minima: existe ou nao existe, nao importa o conteudo.
        get_db().collection("fatores").limit(1).get()
    except Exception as erro:  # noqa: BLE001 - qualquer falha vale como nao-pronto
        resposta.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "indisponivel", "dependencia": "firestore", "erro": str(erro)}

    return {"status": "pronto", "dependencia": "firestore"}

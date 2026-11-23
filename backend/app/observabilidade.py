"""Registros de requisições sem tokens, corpos ou dados pessoais."""

import json
import logging
import sys
from time import perf_counter
from uuid import uuid4

from fastapi import Request

logger = logging.getLogger("carbontrace.requisicoes")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


async def registrar_requisicao(request: Request, call_next):
    inicio = perf_counter()
    request_id = str(uuid4())
    codigo = 500

    try:
        resposta = await call_next(request)
        codigo = resposta.status_code
        resposta.headers["X-Request-ID"] = request_id
        return resposta
    finally:
        rota = request.scope.get("route")
        gravidade = (
            "ERROR" if codigo >= 500
            else "WARNING" if codigo >= 400
            else "INFO"
        )
        registro = {
            "gravidade": gravidade,
            "requestId": request_id,
            "rota": getattr(rota, "path", "<sem_rota>"),
            "status": codigo,
            "latenciaMs": round((perf_counter() - inicio) * 1000, 2),
            "tenantId": getattr(request.state, "tenant_id", None),
        }
        logger.info(json.dumps(registro, ensure_ascii=False))

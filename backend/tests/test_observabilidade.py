"""Verifica correlação, contexto e privacidade dos logs."""

import json
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import Identidade, funcionario_atual, identidade_atual
from app.observabilidade import logger, registrar_requisicao


@pytest.fixture
def cliente_logs(caplog):
    app = FastAPI()
    app.middleware("http")(registrar_requisicao)

    app.dependency_overrides[identidade_atual] = lambda: Identidade(
        uid="usuario-teste",
        tenant_id="empresa-a",
        papel="funcionario",
        email="pessoa@example.test",
    )

    @app.get("/healthz")
    def saude():
        return {"status": "ok"}

    @app.post("/teste/{codigo}")
    def protegido(
        codigo: str,
        pessoa: Identidade = Depends(funcionario_atual),
    ):
        return {"status": "ok"}

    @app.get("/falha")
    def falha():
        raise RuntimeError("detalhe-interno-confidencial")

    logger.addHandler(caplog.handler)
    caplog.set_level("INFO", logger=logger.name)
    try:
        with TestClient(app, raise_server_exceptions=False) as cliente:
            yield cliente, caplog
    finally:
        logger.removeHandler(caplog.handler)


def ultimo_registro(caplog):
    registros = [
        r for r in caplog.records
        if r.name == "carbontrace.requisicoes"
    ]
    return json.loads(registros[-1].getMessage())


def test_saude_tem_correlacao_sem_tenant(cliente_logs):
    cliente, caplog = cliente_logs
    resposta = cliente.get("/healthz")
    registro = ultimo_registro(caplog)

    assert resposta.status_code == 200
    assert registro["status"] == 200
    assert registro["gravidade"] == "INFO"
    assert registro["rota"] == "/healthz"
    assert registro["tenantId"] is None
    assert registro["latenciaMs"] >= 0
    assert registro["requestId"] == resposta.headers["X-Request-ID"]
    UUID(registro["requestId"])


def test_rota_autorizada_registra_tenant_sem_dados_sensiveis(cliente_logs):
    cliente, caplog = cliente_logs
    resposta = cliente.post(
        "/teste/codigo-confidencial?segredo=valor-confidencial",
        headers={"Authorization": "Bearer token-confidencial"},
        json={"email": "pessoa@example.test", "senha": "senha-confidencial"},
    )
    registro = ultimo_registro(caplog)

    assert resposta.status_code == 200
    assert registro["tenantId"] == "empresa-a"
    assert registro["rota"] == "/teste/{codigo}"

    texto = json.dumps(registro)
    for valor in (
        "codigo-confidencial",
        "valor-confidencial",
        "token-confidencial",
        "pessoa@example.test",
        "senha-confidencial",
    ):
        assert valor not in texto


def test_falha_registra_500_sem_detalhes_internos(cliente_logs):
    cliente, caplog = cliente_logs
    resposta = cliente.get("/falha")
    registro = ultimo_registro(caplog)

    assert resposta.status_code == 500
    assert registro["status"] == 500
    assert registro["gravidade"] == "ERROR"
    assert registro["tenantId"] is None
    assert "detalhe-interno-confidencial" not in json.dumps(registro)

"""Prova de vida da API. Nao precisa de Firestore."""

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde_200():
    resposta = cliente.get("/health")
    assert resposta.status_code == 200


def test_health_devolve_status_ok():
    assert cliente.get("/health").json()["status"] == "ok"


def test_openapi_e_gerado():
    """O contrato da API e publicado automaticamente pelo FastAPI."""
    resposta = cliente.get("/openapi.json")
    assert resposta.status_code == 200
    assert "/v1/unidades" in resposta.json()["paths"]

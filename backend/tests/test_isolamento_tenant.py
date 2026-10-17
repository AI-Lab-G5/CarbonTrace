"""Isolamento entre empresas clientes.

Requisito do Checkpoint 1: o teste precisa existir mesmo que falhe
enquanto o sistema nao esta pronto. Ele verifica que um usuario da
empresa A recebe 403 ou 404 ao tentar alcancar dados da empresa B.

Para rodar e preciso o emulador do Firestore no ar:

    firebase emulators:start --only firestore
    FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 pytest tests/test_isolamento_tenant.py

Sem o emulador, os testes sao pulados em vez de falharem por engano --
falha vermelha tem de significar "regra quebrada", nunca "faltou setup".
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.skipif(
    not os.environ.get("FIRESTORE_EMULATOR_HOST"),
    reason="Requer o emulador do Firestore (FIRESTORE_EMULATOR_HOST).",
)

cliente = TestClient(app)

EMPRESA_A = {"X-Debug-Uid": "ana", "X-Debug-Tenant": "empresa-a", "X-Debug-Papel": "gestor"}
EMPRESA_B = {"X-Debug-Uid": "bruno", "X-Debug-Tenant": "empresa-b", "X-Debug-Papel": "gestor"}


@pytest.fixture
def unidade_da_empresa_a() -> str:
    resposta = cliente.post(
        "/v1/unidades",
        headers=EMPRESA_A,
        json={"nome": "Loja Centro", "cidade": "Brasilia", "uf": "DF"},
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def test_empresa_b_nao_enxerga_unidade_da_empresa_a(unidade_da_empresa_a: str):
    resposta = cliente.get(f"/v1/unidades/{unidade_da_empresa_a}", headers=EMPRESA_B)
    assert resposta.status_code in (403, 404)


def test_listagem_nao_mistura_empresas(unidade_da_empresa_a: str):
    ids_vistos_por_b = {u["id"] for u in cliente.get("/v1/unidades", headers=EMPRESA_B).json()}
    assert unidade_da_empresa_a not in ids_vistos_por_b


def test_empresa_b_nao_lanca_registro_em_unidade_alheia(unidade_da_empresa_a: str):
    resposta = cliente.put(
        "/v1/registros",
        headers=EMPRESA_B,
        json={
            "unidade_id": unidade_da_empresa_a,
            "competencia": "2026-01",
            "fonte_id": "energia_eletrica_sin",
            "quantidade": 100,
        },
    )
    assert resposta.status_code in (403, 404)


def test_consolidado_da_empresa_b_ignora_dados_da_empresa_a(unidade_da_empresa_a: str):
    cliente.put(
        "/v1/registros",
        headers=EMPRESA_A,
        json={
            "unidade_id": unidade_da_empresa_a,
            "competencia": "2026-01",
            "fonte_id": "energia_eletrica_sin",
            "quantidade": 1000,
        },
    )
    consolidado_b = cliente.get("/v1/consolidado?competencia=2026-01", headers=EMPRESA_B).json()
    assert consolidado_b["total_kg_co2e"] == 0.0


def test_requisicao_sem_identidade_e_rejeitada():
    assert cliente.get("/v1/unidades").status_code == 401


def test_papel_leitor_nao_grava():
    resposta = cliente.post(
        "/v1/unidades",
        headers={"X-Debug-Uid": "carla", "X-Debug-Tenant": "empresa-a", "X-Debug-Papel": "leitor"},
        json={"nome": "Loja Sul", "cidade": "Brasilia", "uf": "DF"},
    )
    assert resposta.status_code == 403

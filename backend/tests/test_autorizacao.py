"""Os quatro testes de autorizacao, para cada rota protegida.

Exigencia do guia do CP2: sem token, token expirado, papel errado e
empresa errada. Os tres primeiros nao tocam no Firestore e rodam em
qualquer CI. O quarto precisa de dado gravado para ser verificavel e
esta em test_isolamento_tenant.py, com o emulador.

As rotas publicas (/healthz e /readyz) entram aqui tambem, para provar
que continuam abertas -- uma excecao nao declarada e tao perigosa
quanto uma rota desprotegida.
"""

import pytest
from fastapi.testclient import TestClient

# (metodo, caminho, corpo) de toda rota que exige autenticacao.
ROTAS_PROTEGIDAS = [
    ("GET", "/v1/unidades", None),
    ("GET", "/v1/unidades/abc123", None),
    ("POST", "/v1/unidades", {"nome": "Loja", "cidade": "Brasilia", "uf": "DF"}),
    ("GET", "/v1/fontes", None),
    ("GET", "/v1/fontes/versoes", None),
    ("GET", "/v1/fontes/versoes/v1", None),
    ("GET", "/v1/consumos", None),
    ("GET", "/v1/consumos/abc123", None),
    (
        "PUT",
        "/v1/consumos",
        {
            "unidade_id": "abc123",
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    ),
    ("POST", "/v1/consumos/abc123/recalculo", None),
    ("GET", "/v1/consolidado?competencia=2026-01", None),
]

ROTAS_PUBLICAS = ["/healthz", "/readyz"]


def _chamar(cliente: TestClient, metodo: str, caminho: str, corpo):
    return cliente.request(metodo, caminho, json=corpo)


@pytest.mark.parametrize("metodo,caminho,corpo", ROTAS_PROTEGIDAS)
def test_sem_token_e_barrado(cliente, metodo, caminho, corpo):
    resposta = _chamar(cliente, metodo, caminho, corpo)
    assert resposta.status_code == 401, (
        f"{metodo} {caminho} respondeu {resposta.status_code} sem token."
    )


@pytest.mark.parametrize("metodo,caminho,corpo", ROTAS_PROTEGIDAS)
def test_token_expirado_e_barrado(com_token_expirado, metodo, caminho, corpo):
    resposta = _chamar(com_token_expirado, metodo, caminho, corpo)
    assert resposta.status_code == 401
    assert "expirado" in resposta.json()["detail"].lower()


@pytest.mark.parametrize("metodo,caminho,corpo", ROTAS_PROTEGIDAS)
def test_papel_errado_e_barrado(com_papel_errado, metodo, caminho, corpo):
    resposta = _chamar(com_papel_errado, metodo, caminho, corpo)
    assert resposta.status_code == 403, (
        f"{metodo} {caminho} respondeu {resposta.status_code} com papel invalido."
    )


@pytest.mark.parametrize("metodo,caminho,corpo", ROTAS_PROTEGIDAS)
def test_usuario_sem_empresa_e_barrado(sem_empresa, metodo, caminho, corpo):
    """Token legitimo de quem ainda nao foi vinculado a uma empresa.

    Sem este caso, um usuario recem-criado cairia no caminho de consulta
    com tenant None e o comportamento seria indefinido.
    """
    resposta = _chamar(sem_empresa, metodo, caminho, corpo)
    assert resposta.status_code == 403


@pytest.mark.parametrize("caminho", ROTAS_PUBLICAS)
def test_rotas_publicas_respondem_sem_token(cliente, caminho):
    resposta = cliente.get(caminho)
    assert resposta.status_code in (200, 503), (
        f"{caminho} deveria ser publica, respondeu {resposta.status_code}."
    )


def test_bearer_vazio_e_barrado(cliente):
    resposta = cliente.get("/v1/unidades", headers={"Authorization": "Bearer "})
    assert resposta.status_code == 401


def test_esquema_errado_e_barrado(cliente):
    """Basic no lugar de Bearer."""
    resposta = cliente.get("/v1/unidades", headers={"Authorization": "Basic YWJjOjEyMw=="})
    assert resposta.status_code == 401

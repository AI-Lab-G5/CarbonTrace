"""Empresa errada: o quarto teste de autorizacao de cada rota.

Precisa de dado gravado para ser verificavel -- "barrar acesso ao
registro da empresa A" so prova alguma coisa se o registro existir.
Por isso estes casos usam o duble de Firestore em memoria, e nao o
conjunto puro.

O isolamento aqui e o da aplicacao: dado que mora sob
/tenants/{id}/..., consultado sempre pelo caminho do tenant de quem
chama. A segunda camada -- as regras do Firestore, que barram mesmo
quem falasse direto com o banco -- e verificada contra o emulador pelo
QA, na issue #24.
"""

import pytest

pytestmark = pytest.mark.precisa_banco


@pytest.fixture
def unidade_da_empresa_a(como_funcionario) -> str:
    resposta = como_funcionario.post(
        "/v1/unidades",
        json={"nome": "Loja Centro", "cidade": "Brasilia", "uf": "DF"},
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


@pytest.fixture
def consumo_da_empresa_a(como_funcionario, unidade_da_empresa_a) -> str:
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade_da_empresa_a,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 200
    return resposta.json()["id"]


# --------------------------------------------------------------------
# Acesso por ID a recurso de outra empresa
# --------------------------------------------------------------------


def test_unidade_de_outra_empresa_nao_e_acessivel(
    como_outra_empresa, unidade_da_empresa_a
):
    """404 e nao 403: distinguir os dois revelaria quais ids existem."""
    resposta = como_outra_empresa.get(f"/v1/unidades/{unidade_da_empresa_a}")
    assert resposta.status_code == 404


def test_consumo_de_outra_empresa_nao_e_acessivel(
    como_outra_empresa, consumo_da_empresa_a
):
    resposta = como_outra_empresa.get(f"/v1/consumos/{consumo_da_empresa_a}")
    assert resposta.status_code == 404


def test_recalculo_de_consumo_alheio_e_barrado(
    como_outra_empresa, consumo_da_empresa_a
):
    resposta = como_outra_empresa.post(
        f"/v1/consumos/{consumo_da_empresa_a}/recalculo"
    )
    assert resposta.status_code == 404


# --------------------------------------------------------------------
# Listagens nao vazam entre empresas
# --------------------------------------------------------------------


def test_listagem_de_unidades_nao_mistura(como_outra_empresa, unidade_da_empresa_a):
    pagina = como_outra_empresa.get("/v1/unidades").json()
    vistos = {u["id"] for u in pagina["itens"]}
    assert unidade_da_empresa_a not in vistos


def test_listagem_de_consumos_nao_mistura(como_outra_empresa, consumo_da_empresa_a):
    pagina = como_outra_empresa.get("/v1/consumos").json()
    vistos = {c["id"] for c in pagina["itens"]}
    assert consumo_da_empresa_a not in vistos


# --------------------------------------------------------------------
# Escrita cruzada
# --------------------------------------------------------------------


def test_nao_lanca_consumo_em_unidade_alheia(
    como_outra_empresa, unidade_da_empresa_a
):
    """O id da unidade e da empresa A; quem chama e da B.

    A consulta busca a unidade sob o caminho da empresa B, nao encontra,
    e devolve 404 -- o isolamento vem da estrutura, nao de uma checagem
    que alguem poderia esquecer de escrever.
    """
    resposta = como_outra_empresa.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade_da_empresa_a,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "100",
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 404


def test_consolidado_de_outra_empresa_ignora_dados_alheios(
    como_outra_empresa, consumo_da_empresa_a
):
    consolidado = como_outra_empresa.get(
        "/v1/consolidado?competencia=2026-01"
    ).json()
    assert consolidado["total_kg_co2e"] == "0.000"
    assert consolidado["por_unidade"] == []

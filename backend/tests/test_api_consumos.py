"""Fluxo ponta a ponta de J1, J2 e J3.

Cadastra unidade, lanca consumo, confere o calculo e o recalculo.
Complementa os testes de dominio: la a conta e pura, aqui ela passa
por HTTP, persistencia e de volta -- e e onde um erro de serializacao
apareceria.

Roda contra o duble de Firestore em memoria, descrito em
tests/duble_firestore.py, com banco limpo a cada teste. Os fatores sao
os do catalogo real em docs/dados, nao valores inventados aqui: e o que
permite conferir os numeros a mao.
"""

import pytest

pytestmark = pytest.mark.precisa_banco


@pytest.fixture
def unidade(como_funcionario) -> str:
    resposta = como_funcionario.post(
        "/v1/unidades",
        json={"nome": "Loja Asa Norte", "cidade": "Brasilia", "uf": "DF"},
    )
    return resposta.json()["id"]


def test_fluxo_completo_de_lancamento(como_funcionario, unidade):
    """1500 kWh x 0,0426 = 63,900 kgCO2e, conferido a mao.

    A competencia e de 2026, entao vale a v2 (0,0426) e nao a v1
    (0,0385). Nao e detalhe: e o motivo de o fator viajar junto do
    lancamento em vez de ser consultado na hora de ler.
    """
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["emissao_kg_co2e"] == "63.900"
    assert corpo["fator_valor"] == "0.0426"
    assert corpo["escopo"] == "2"


def test_numeros_trafegam_como_texto(como_funcionario, unidade):
    """CA-02 na saida: nenhum numero sai como decimal JSON.

    Se um deles virasse float, o front receberia 57.75000000000001 em
    algum caso e a conferencia com a planilha deixaria de bater.
    """
    corpo = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "diesel",
            "quantidade": "350.5",
            "unidade_medida": "L",
        },
    ).json()

    for campo in (
        "quantidade_informada",
        "quantidade_convertida",
        "fator_valor",
        "emissao_kg_co2e",
    ):
        assert isinstance(corpo[campo], str), f"{campo} saiu como {type(corpo[campo])}"


def test_mwh_e_convertido_antes_do_calculo(como_funcionario, unidade):
    """2,5 MWh = 2500 kWh x 0,0426 = 106,500."""
    corpo = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "2.5",
            "unidade_medida": "MWh",
        },
    ).json()

    assert corpo["unidade_informada"] == "MWh"
    assert corpo["quantidade_convertida"] == "2500.0"
    assert corpo["unidade_base"] == "kWh"
    assert corpo["emissao_kg_co2e"] == "106.500"


def test_lancamento_repetido_sobrescreve(como_funcionario, unidade):
    """Idempotencia: duplo clique nao vira consumo em dobro (ADR-006)."""
    pedido = {
        "unidade_id": unidade,
        "competencia": "2026-02",
        "fonte_id": "eletricidade",
        "quantidade": "1000",
        "unidade_medida": "kWh",
    }
    primeiro = como_funcionario.put("/v1/consumos", json=pedido).json()
    segundo = como_funcionario.put("/v1/consumos", json=pedido).json()

    assert primeiro["id"] == segundo["id"]

    pagina = como_funcionario.get("/v1/consumos?competencia=2026-02").json()
    assert len([c for c in pagina["itens"] if c["unidade_id"] == unidade]) == 1


def test_correcao_substitui_o_valor_anterior(como_funcionario, unidade):
    base = {
        "unidade_id": unidade,
        "competencia": "2026-03",
        "fonte_id": "eletricidade",
        "unidade_medida": "kWh",
    }
    como_funcionario.put("/v1/consumos", json={**base, "quantidade": "10000"})
    corrigido = como_funcionario.put(
        "/v1/consumos", json={**base, "quantidade": "1000"}
    ).json()

    assert corrigido["emissao_kg_co2e"] == "42.600"


def test_recalculo_devolve_o_mesmo_numero(como_funcionario, unidade):
    """Prova do CA-03 pela API.

    O endpoint refaz a conta com o fator que o lancamento registrou e
    compara com o gravado. Divergencia vira 500, porque seria defeito
    nosso, nao erro de quem chamou.
    """
    consumo = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-04",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    ).json()

    refeito = como_funcionario.post(f"/v1/consumos/{consumo['id']}/recalculo")
    assert refeito.status_code == 200
    assert refeito.json()["emissao_kg_co2e"] == consumo["emissao_kg_co2e"]


def test_competencia_de_2025_usa_a_versao_de_2025(como_funcionario, unidade):
    """Lancamento antigo usa o fator da epoca, nao o mais recente.

    Com a v2 publicada e vigente desde 2026-01, um lancamento de 2025
    continua na v1. E o que permite reabrir o inventario do ano passado
    e encontrar os mesmos numeros.
    """
    corpo = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2025-06",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    ).json()

    assert corpo["fator_versao"] == "v1"
    assert corpo["fator_valor"] == "0.0385"
    assert corpo["emissao_kg_co2e"] == "57.750"


def test_competencia_de_2026_usa_a_versao_nova(como_funcionario, unidade):
    """Mesma quantidade, fator diferente: 1500 x 0,0426 = 63,900."""
    corpo = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-05",
            "fonte_id": "eletricidade",
            "quantidade": "1500",
            "unidade_medida": "kWh",
        },
    ).json()

    assert corpo["fator_versao"] == "v2"
    assert corpo["emissao_kg_co2e"] == "63.900"


# --------------------------------------------------------------------
# Erros de dominio chegam como 422, com mensagem util
# --------------------------------------------------------------------


def test_zero_e_gravado_como_lancamento(como_funcionario, unidade):
    """CA-03 da #11: zero e aceito e persiste, com emissao zero."""
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-06",
            "fonte_id": "diesel",
            "quantidade": "0",
            "unidade_medida": "L",
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["emissao_kg_co2e"] == "0.000"

    # Precisa aparecer na listagem: um mes declarado como zero e
    # justamente o que distingue inventario completo de inventario
    # com lacuna.
    pagina = como_funcionario.get("/v1/consumos?competencia=2026-06").json()
    assert any(c["unidade_id"] == unidade for c in pagina["itens"])


@pytest.mark.parametrize(
    "quantidade,trecho",
    [("-5", "negativa"), ("99999999", "teto")],
)
def test_quantidade_fora_das_regras(como_funcionario, unidade, quantidade, trecho):
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": quantidade,
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 422
    assert trecho in resposta.json()["detail"].lower()


def test_unidade_de_medida_incompativel(como_funcionario, unidade):
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "100",
            "unidade_medida": "L",
        },
    )
    assert resposta.status_code == 422
    assert "kWh" in resposta.json()["detail"]


def test_fonte_fora_do_catalogo(como_funcionario, unidade):
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-01",
            "fonte_id": "carvao_mineral",
            "quantidade": "100",
            "unidade_medida": "kg",
        },
    )
    assert resposta.status_code == 422
    assert "fator" in resposta.json()["detail"].lower()


def test_unidade_inexistente(como_funcionario):
    resposta = como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": "nao-existe",
            "competencia": "2026-01",
            "fonte_id": "eletricidade",
            "quantidade": "100",
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 404


# --------------------------------------------------------------------
# Catalogo de fontes (J1)
# --------------------------------------------------------------------


def test_catalogo_traz_as_quatro_fontes_aprovadas(como_funcionario):
    fontes = como_funcionario.get("/v1/fontes?competencia=2026-01").json()
    assert {f["fonte_id"] for f in fontes} == {
        "eletricidade",
        "diesel",
        "gasolina",
        "glp",
    }


def test_catalogo_informa_as_unidades_aceitas(como_funcionario):
    """O front monta o seletor de unidade a partir daqui."""
    fontes = como_funcionario.get("/v1/fontes?competencia=2026-01").json()
    por_id = {f["fonte_id"]: f for f in fontes}

    assert por_id["eletricidade"]["unidades_aceitas"] == ["kWh", "MWh"]
    assert por_id["diesel"]["unidades_aceitas"] == ["L"]
    assert por_id["glp"]["unidades_aceitas"] == ["kg"]


def test_catalogo_marca_o_status_preliminar(como_funcionario):
    """Enquanto os fatores nao forem conferidos na fonte oficial,
    a interface precisa poder avisar que o numero e preliminar."""
    fontes = como_funcionario.get("/v1/fontes?competencia=2026-01").json()
    assert all(f["status"] == "preliminar" for f in fontes)


def test_consolidado_soma_a_rede(como_funcionario, unidade):
    como_funcionario.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade,
            "competencia": "2026-07",
            "fonte_id": "eletricidade",
            "quantidade": "1000",
            "unidade_medida": "kWh",
        },
    )
    consolidado = como_funcionario.get(
        "/v1/consolidado?competencia=2026-07"
    ).json()

    assert consolidado["total_kg_co2e"] == "42.600"
    assert len(consolidado["por_unidade"]) >= 1

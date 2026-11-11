"""Snapshots e agregados pela API -- Jornada 4 (issue #35).

Cobre o que o dominio sozinho nao pode provar: que a leitura nao grava,
que reenviar nao duplica, que versoes anteriores ficam, que a paginacao
respeita 20/100 e que empresa nenhuma ve o snapshot da outra.
"""

import pytest

pytestmark = pytest.mark.precisa_banco

# 1500 kWh x 0,0426 (v2, vigente em 2026) = 63,900, conferido a mao.
EMISSAO_1500_KWH = "63.900"


def _criar_unidade(cliente, nome, uf="DF"):
    resposta = cliente.post(
        "/v1/unidades", json={"nome": nome, "cidade": "Brasilia", "uf": uf}
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _lancar(cliente, unidade_id, competencia, quantidade, fonte="eletricidade"):
    unidade_medida = {"eletricidade": "kWh", "diesel": "L", "glp": "kg"}[fonte]
    resposta = cliente.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade_id,
            "competencia": competencia,
            "fonte_id": fonte,
            "quantidade": quantidade,
            "unidade_medida": unidade_medida,
        },
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


@pytest.fixture
def rede(como_funcionario):
    """Tres unidades em duas regioes, com lancamentos em dois meses.

    E o cenario minimo que o CA-04 pede, montado pela API de verdade.
    """
    unidades = {
        "a": _criar_unidade(como_funcionario, "Loja Asa Norte", "DF"),
        "b": _criar_unidade(como_funcionario, "Loja Taguatinga", "DF"),
        "c": _criar_unidade(como_funcionario, "Centro de Distribuicao", "GO"),
    }
    for apelido, quantidade in (("a", "1500"), ("b", "1000"), ("c", "3000")):
        _lancar(como_funcionario, unidades[apelido], "2026-01", quantidade)
    _lancar(como_funcionario, unidades["a"], "2026-02", "2000")
    return unidades


# --------------------------------------------------------------------
# Geracao
# --------------------------------------------------------------------


def test_gerar_cria_a_primeira_versao(como_funcionario, rede):
    resposta = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    )
    assert resposta.status_code == 201

    corpo = resposta.json()
    assert corpo["criado"] is True
    assert corpo["snapshot"]["id"] == "2026-01_v001"
    assert corpo["snapshot"]["versao"] == 1
    assert corpo["snapshot"]["unidades_no_total"] == 3


def test_total_conferido_a_mao(como_funcionario, rede):
    """1500 + 1000 + 3000 kWh x 0,0426 = 63,900 + 42,600 + 127,800."""
    corpo = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()
    assert corpo["snapshot"]["total_kg_co2e"] == "234.300"


def test_numeros_saem_como_texto(como_funcionario, rede):
    """CA-02 tambem no agregado: nenhum total sai como decimal JSON."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    assert isinstance(snap["total_kg_co2e"], str)
    assert all(isinstance(r["emissao_kg_co2e"], str) for r in snap["por_regiao"])
    assert all(isinstance(e["emissao_kg_co2e"], str) for e in snap["por_escopo"])


def test_regiao_vem_da_uf(como_funcionario, rede):
    """DF soma duas lojas (63,900 + 42,600); GO tem uma (127,800)."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    por_regiao = {r["regiao"]: r for r in snap["por_regiao"]}
    assert por_regiao["DF"]["emissao_kg_co2e"] == "106.500"
    assert por_regiao["DF"]["unidades"] == 2
    assert por_regiao["GO"]["emissao_kg_co2e"] == "127.800"
    assert por_regiao["GO"]["unidades"] == 1


def test_recortes_batem_com_o_total_pela_api(como_funcionario, rede):
    """CA-04 ponta a ponta: a igualdade sobrevive ao ir e voltar do banco.

    E o que o teste de dominio nao alcanca -- se a serializacao perdesse
    uma casa em algum lugar, apareceria aqui.
    """
    from decimal import Decimal

    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    total = Decimal(snap["total_kg_co2e"])
    por_regiao = sum(Decimal(r["emissao_kg_co2e"]) for r in snap["por_regiao"])
    por_escopo = sum(Decimal(e["emissao_kg_co2e"]) for e in snap["por_escopo"])

    unidades = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?limite=100"
    ).json()
    por_unidade = sum(Decimal(u["emissao_kg_co2e"]) for u in unidades["itens"])

    assert total == por_regiao == por_escopo == por_unidade


def test_meses_sao_independentes(como_funcionario, rede):
    janeiro = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]
    fevereiro = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-02"}
    ).json()["snapshot"]

    assert janeiro["total_kg_co2e"] == "234.300"
    assert fevereiro["total_kg_co2e"] == "85.200"
    assert fevereiro["unidades_no_total"] == 1


def test_competencia_invalida_e_recusada(como_funcionario):
    assert (
        como_funcionario.post(
            "/v1/snapshots", json={"competencia": "2026-13"}
        ).status_code
        == 422
    )


# --------------------------------------------------------------------
# CA-03: reenvio nao duplica, versao anterior fica
# --------------------------------------------------------------------


def test_reenviar_sem_mudanca_nao_cria_versao_nova(como_funcionario, rede):
    """A regra de reenvio do CA-03, dita em numeros."""
    primeiro = como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    segundo = como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})

    assert primeiro.status_code == 201
    assert segundo.status_code == 200
    assert segundo.json()["criado"] is False
    assert segundo.json()["snapshot"]["id"] == primeiro.json()["snapshot"]["id"]

    lista = como_funcionario.get("/v1/snapshots?competencia=2026-01").json()
    assert lista["total_na_pagina"] == 1


def test_mudanca_no_lancamento_cria_versao_nova(como_funcionario, rede):
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    _lancar(como_funcionario, rede["a"], "2026-01", "5000")

    segundo = como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    assert segundo.status_code == 201
    assert segundo.json()["snapshot"]["id"] == "2026-01_v002"
    assert segundo.json()["snapshot"]["versao"] == 2


def test_versao_anterior_e_preservada(como_funcionario, rede):
    """CA-04: snapshots anteriores continuam la, com o numero da epoca.

    E o que separa snapshot de cache: o historico publicado nao muda
    quando o dado de origem muda.
    """
    primeiro = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    _lancar(como_funcionario, rede["a"], "2026-01", "5000")
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})

    antigo = como_funcionario.get(f"/v1/snapshots/{primeiro['id']}")
    assert antigo.status_code == 200
    assert antigo.json()["total_kg_co2e"] == "234.300"

    lista = como_funcionario.get("/v1/snapshots?competencia=2026-01").json()
    assert {s["id"] for s in lista["itens"]} == {"2026-01_v001", "2026-01_v002"}


def test_impressao_digital_muda_com_o_conteudo(como_funcionario, rede):
    primeiro = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]
    _lancar(como_funcionario, rede["a"], "2026-01", "5000")
    segundo = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    assert primeiro["impressao_digital"] != segundo["impressao_digital"]


def test_leitura_nunca_gera_snapshot(como_funcionario, rede):
    """CA-03 em letra: consulta nao dispara escrita.

    Varias leituras depois da geracao, e a contagem de snapshots nao se
    mexe. Um GET que gerasse sob demanda passaria em todo teste de
    conteudo e falharia aqui.
    """
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    for _ in range(3):
        como_funcionario.get(f"/v1/snapshots/{snap['id']}")
        como_funcionario.get(f"/v1/snapshots/{snap['id']}/unidades")
        como_funcionario.get(f"/v1/snapshots/{snap['id']}/comparacao")
        como_funcionario.get("/v1/agregados?competencia=2026-01")
        como_funcionario.get("/v1/snapshots")

    lista = como_funcionario.get("/v1/snapshots?competencia=2026-01").json()
    assert lista["total_na_pagina"] == 1


def test_competencia_sem_snapshot_nao_gera_na_leitura(como_funcionario, rede):
    """404 e a resposta certa: gerar seria escrita escondida num GET."""
    resposta = como_funcionario.get("/v1/agregados?competencia=2026-03")
    assert resposta.status_code == 404
    assert "POST /v1/snapshots" in resposta.json()["detail"]


def test_agregado_vigente_e_a_maior_versao(como_funcionario, rede):
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    _lancar(como_funcionario, rede["a"], "2026-01", "5000")
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})

    vigente = como_funcionario.get("/v1/agregados?competencia=2026-01").json()
    assert vigente["id"] == "2026-01_v002"
    assert vigente["versao"] == 2


# --------------------------------------------------------------------
# CA-07: paginacao 20/100 e filtros
# --------------------------------------------------------------------


def test_limite_padrao_e_vinte(como_funcionario, rede):
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]
    pagina = como_funcionario.get(f"/v1/snapshots/{snap['id']}/unidades").json()
    assert pagina["limite"] == 20


def test_limite_acima_de_cem_e_recusado(como_funcionario, rede):
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]
    resposta = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?limite=101"
    )
    assert resposta.status_code == 422


def test_total_nao_depende_da_pagina(como_funcionario, rede):
    """CA-07: o total vem do snapshot, nao da soma da pagina aberta."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    pagina = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?limite=1"
    ).json()
    assert pagina["total_na_pagina"] == 1
    assert pagina["proximo_cursor"] is not None

    cabecalho = como_funcionario.get(f"/v1/snapshots/{snap['id']}").json()
    assert cabecalho["total_kg_co2e"] == "234.300"
    assert cabecalho["unidades_no_total"] == 3


def test_percorrer_as_paginas_cobre_a_rede(como_funcionario, rede):
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    vistos, cursor, voltas = [], None, 0
    while True:
        url = f"/v1/snapshots/{snap['id']}/unidades?limite=2"
        if cursor:
            url += f"&cursor={cursor}"
        pagina = como_funcionario.get(url).json()
        vistos.extend(u["unidade_id"] for u in pagina["itens"])
        cursor = pagina["proximo_cursor"]
        voltas += 1
        if cursor is None:
            break
        assert voltas < 10

    assert len(vistos) == 3
    assert len(set(vistos)) == 3


def test_filtro_por_regiao(como_funcionario, rede):
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    df = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?regiao=DF"
    ).json()
    assert df["total_na_pagina"] == 2
    assert all(u["regiao"] == "DF" for u in df["itens"])

    go = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?regiao=go"
    ).json()
    assert go["total_na_pagina"] == 1


def test_posicao_do_ranking_vem_gravada(como_funcionario, rede):
    """A ordem nao pode depender de quem leu nem de como paginou."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    itens = como_funcionario.get(
        f"/v1/snapshots/{snap['id']}/unidades?limite=100"
    ).json()["itens"]
    por_posicao = {u["posicao"]: u["emissao_kg_co2e"] for u in itens}

    assert por_posicao[1] == "127.800"
    assert por_posicao[3] == "42.600"


# --------------------------------------------------------------------
# CA-06: comparacao
# --------------------------------------------------------------------


def test_comparacao_com_tres_elegiveis(como_funcionario, rede):
    """Mediana de 42,600, 63,900 e 127,800 = 63,900."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    comp = como_funcionario.get(f"/v1/snapshots/{snap['id']}/comparacao").json()
    assert comp["disponivel"] is True
    assert comp["elegiveis"] == 3
    assert comp["mediana_kg_co2e"] == "63.900"
    assert comp["linhas"][0]["unidade_id"] == rede["c"]


def test_comparacao_indisponivel_com_poucas_unidades(como_funcionario, rede):
    """Fevereiro tem uma unidade so: nao ha base de comparacao."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-02"}
    ).json()["snapshot"]

    comp = como_funcionario.get(f"/v1/snapshots/{snap['id']}/comparacao").json()
    assert comp["disponivel"] is False
    assert "3 unidades" in comp["motivo"]
    assert comp["linhas"] == []


def test_alerta_em_desvio_grande(como_funcionario, rede):
    """127,800 contra mediana 63,900 = +100%: passa dos 50%."""
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    comp = como_funcionario.get(f"/v1/snapshots/{snap['id']}/comparacao").json()
    por_id = {linha["unidade_id"]: linha for linha in comp["linhas"]}
    assert por_id[rede["c"]]["desvio_percentual"] == "100.00"
    assert por_id[rede["c"]]["alerta"] is True
    assert por_id[rede["a"]]["alerta"] is False


# --------------------------------------------------------------------
# Isolamento entre empresas
# --------------------------------------------------------------------


def test_snapshot_de_outra_empresa_nao_e_acessivel(
    como_funcionario, como_outra_empresa, rede
):
    snap = como_funcionario.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    assert como_outra_empresa.get(f"/v1/snapshots/{snap['id']}").status_code == 404
    assert (
        como_outra_empresa.get(
            f"/v1/snapshots/{snap['id']}/unidades"
        ).status_code
        == 404
    )
    assert (
        como_outra_empresa.get(
            f"/v1/snapshots/{snap['id']}/comparacao"
        ).status_code
        == 404
    )


def test_listagem_de_snapshots_nao_mistura(
    como_funcionario, como_outra_empresa, rede
):
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    lista = como_outra_empresa.get("/v1/snapshots").json()
    assert lista["itens"] == []


def test_agregado_vigente_nao_vaza_entre_empresas(
    como_funcionario, como_outra_empresa, rede
):
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})
    resposta = como_outra_empresa.get("/v1/agregados?competencia=2026-01")
    assert resposta.status_code == 404


def test_empresa_b_gera_o_proprio_snapshot_sem_ver_a_a(
    como_funcionario, como_outra_empresa, rede
):
    """Mesma competencia, empresas diferentes, totais diferentes."""
    como_funcionario.post("/v1/snapshots", json={"competencia": "2026-01"})

    unidade_b = _criar_unidade(como_outra_empresa, "Loja da Empresa B", "SP")
    _lancar(como_outra_empresa, unidade_b, "2026-01", "1000")

    snap_b = como_outra_empresa.post(
        "/v1/snapshots", json={"competencia": "2026-01"}
    ).json()["snapshot"]

    assert snap_b["total_kg_co2e"] == "42.600"
    assert snap_b["unidades_no_total"] == 1

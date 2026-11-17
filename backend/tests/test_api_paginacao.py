"""Listas controladas e paginadas -- CA-05 da issue #11.

O que precisa estar provado: nenhuma listagem devolve tudo, percorrer
as paginas cobre o conjunto inteiro sem repetir nem pular item, e um
cursor de outra empresa nao vira porta de entrada.
"""

import pytest

pytestmark = pytest.mark.precisa_banco

TOTAL = 12


@pytest.fixture
def doze_unidades(como_funcionario) -> list[str]:
    ids = []
    for i in range(TOTAL):
        resposta = como_funcionario.post(
            "/v1/unidades",
            json={"nome": f"Loja {i:02d}", "cidade": "Brasilia", "uf": "DF"},
        )
        ids.append(resposta.json()["id"])
    return ids


def test_limite_padrao_nao_e_ilimitado(como_funcionario):
    """Sem 'limite' na query, ainda assim ha um teto."""
    pagina = como_funcionario.get("/v1/unidades").json()
    assert pagina["limite"] == 50


def test_limite_respeitado(como_funcionario, doze_unidades):
    pagina = como_funcionario.get("/v1/unidades?limite=5").json()
    assert pagina["total_na_pagina"] == 5
    assert len(pagina["itens"]) == 5
    assert pagina["proximo_cursor"] is not None


def test_percorrer_tudo_nao_repete_nem_pula(como_funcionario, doze_unidades):
    """A prova que importa: a soma das paginas e o conjunto, sem sobra.

    Um off-by-one no cursor -- start_at em vez de start_after -- se
    manifesta exatamente aqui, repetindo o ultimo item de cada pagina.
    """
    vistos: list[str] = []
    cursor = None
    paginas = 0

    while True:
        url = "/v1/unidades?limite=5" + (f"&cursor={cursor}" if cursor else "")
        pagina = como_funcionario.get(url).json()
        vistos.extend(u["id"] for u in pagina["itens"])
        paginas += 1
        cursor = pagina["proximo_cursor"]
        if cursor is None:
            break
        assert paginas < 10, "paginacao nao terminou: provavel laco infinito"

    assert len(vistos) == TOTAL
    assert len(set(vistos)) == TOTAL, "algum item veio em duas paginas"
    assert set(vistos) == set(doze_unidades)
    assert paginas == 3  # 5 + 5 + 2


def test_ultima_pagina_nao_oferece_cursor(como_funcionario, doze_unidades):
    """Cursor nulo e o unico sinal de fim que o front tem.

    Devolver um cursor na ultima pagina levaria a uma chamada a mais,
    vazia -- e a um laco infinito em qualquer front que pare so quando
    a lista vier vazia.
    """
    pagina = como_funcionario.get("/v1/unidades?limite=50").json()
    assert pagina["total_na_pagina"] == TOTAL
    assert pagina["proximo_cursor"] is None


def test_limite_acima_do_maximo_e_recusado(como_funcionario):
    """Nao adianta ter teto se o cliente pode pedir 100000."""
    assert como_funcionario.get("/v1/unidades?limite=100000").status_code == 422


def test_limite_zero_ou_negativo_e_recusado(como_funcionario):
    assert como_funcionario.get("/v1/unidades?limite=0").status_code == 422
    assert como_funcionario.get("/v1/unidades?limite=-1").status_code == 422


def test_cursor_inexistente_e_recusado(como_funcionario, doze_unidades):
    """400 e nao uma pagina vazia: pagina vazia parece fim de lista."""
    resposta = como_funcionario.get("/v1/unidades?cursor=nao-existe")
    assert resposta.status_code == 400
    assert "cursor" in resposta.json()["detail"].lower()


def test_cursor_de_outra_empresa_nao_serve(como_outra_empresa, doze_unidades):
    """O cursor e resolvido sob o caminho de quem chama.

    Um id valido da empresa A, usado pela empresa B, nao existe no
    caminho da B -- entao vira 400, nao uma janela para os dados dela.
    """
    resposta = como_outra_empresa.get(f"/v1/unidades?cursor={doze_unidades[0]}")
    assert resposta.status_code == 400


def test_consumos_tambem_sao_paginados(como_funcionario, doze_unidades):
    for i, unidade in enumerate(doze_unidades[:6]):
        como_funcionario.put(
            "/v1/consumos",
            json={
                "unidade_id": unidade,
                "competencia": "2026-02",
                "fonte_id": "eletricidade",
                "quantidade": str(100 + i),
                "unidade_medida": "kWh",
            },
        )

    pagina = como_funcionario.get("/v1/consumos?limite=4").json()
    assert pagina["total_na_pagina"] == 4
    assert pagina["proximo_cursor"] is not None

    segunda = como_funcionario.get(
        f"/v1/consumos?limite=4&cursor={pagina['proximo_cursor']}"
    ).json()
    assert segunda["total_na_pagina"] == 2
    assert segunda["proximo_cursor"] is None

    primeiros = {c["id"] for c in pagina["itens"]}
    segundos = {c["id"] for c in segunda["itens"]}
    assert primeiros.isdisjoint(segundos)


def test_filtro_e_paginacao_convivem(como_funcionario, doze_unidades):
    """Filtrar por competencia e paginar ao mesmo tempo.

    No Firestore de verdade isto combina where com order_by e pode
    exigir indice composto; o duble nao cobre esse aspecto. Fica
    registrado para o QA verificar contra o emulador (issue #24).
    """
    for unidade in doze_unidades[:3]:
        for competencia in ("2026-03", "2026-04"):
            como_funcionario.put(
                "/v1/consumos",
                json={
                    "unidade_id": unidade,
                    "competencia": competencia,
                    "fonte_id": "diesel",
                    "quantidade": "100",
                    "unidade_medida": "L",
                },
            )

    pagina = como_funcionario.get("/v1/consumos?competencia=2026-03&limite=2").json()
    assert pagina["total_na_pagina"] == 2
    assert all(c["competencia"] == "2026-03" for c in pagina["itens"])

    segunda = como_funcionario.get(
        f"/v1/consumos?competencia=2026-03&limite=2&cursor={pagina['proximo_cursor']}"
    ).json()
    assert segunda["total_na_pagina"] == 1
    assert all(c["competencia"] == "2026-03" for c in segunda["itens"])

"""Codigo unico de empresa -- CA-01 da issue #35."""

import pytest

pytestmark = pytest.mark.precisa_banco

NOVA = {"codigo": "padaria-central", "nome": "Padaria Central Ltda"}


def test_cadastro_cria_a_empresa(sem_empresa):
    resposta = sem_empresa.post("/v1/empresas", json=NOVA)
    assert resposta.status_code == 201
    assert resposta.json()["codigo"] == "padaria-central"
    assert resposta.json()["nome"] == "Padaria Central Ltda"


def test_codigo_duplicado_da_conflito(sem_empresa):
    """409, nao sobrescrita silenciosa.

    A garantia vem do `create()` do Firestore: conferir antes e gravar
    depois deixaria uma janela entre as duas operacoes em que dois
    pedidos com o mesmo codigo passariam.
    """
    assert sem_empresa.post("/v1/empresas", json=NOVA).status_code == 201

    repetido = sem_empresa.post(
        "/v1/empresas", json={**NOVA, "nome": "Outra Empresa"}
    )
    assert repetido.status_code == 409
    assert "padaria-central" in repetido.json()["detail"]

    # A primeira continua intacta: o 409 nao encostou nela.
    assert (
        sem_empresa.get("/v1/empresas/padaria-central").json()["nome"]
        == "Padaria Central Ltda"
    )


def test_maiuscula_nao_cria_empresa_diferente(sem_empresa):
    """"ACME" e "acme" seriam duas linhas indistinguiveis na tela."""
    assert sem_empresa.post("/v1/empresas", json=NOVA).status_code == 201
    repetido = sem_empresa.post(
        "/v1/empresas", json={**NOVA, "codigo": "PADARIA-CENTRAL"}
    )
    assert repetido.status_code == 409


def test_autoria_do_cadastro(sem_empresa):
    corpo = sem_empresa.post("/v1/empresas", json=NOVA).json()
    assert corpo["criado_por_uid"] == "novo"
    assert corpo["criado_em"] is not None


@pytest.mark.parametrize(
    "codigo",
    ["ab", "x" * 41, "com barra/", "com espaco", "-comeca-com-hifen", "termina-", ""],
)
def test_codigo_invalido_e_recusado(sem_empresa, codigo):
    resposta = sem_empresa.post("/v1/empresas", json={**NOVA, "codigo": codigo})
    assert resposta.status_code == 422


def test_nome_so_com_espaco_e_recusado(sem_empresa):
    resposta = sem_empresa.post("/v1/empresas", json={**NOVA, "nome": "   "})
    assert resposta.status_code == 422


def test_quem_ja_tem_empresa_nao_cria_outra(como_funcionario):
    """Sem papel administrativo, esta e a restricao possivel hoje.

    Sem ela, qualquer funcionario de qualquer empresa criaria empresas a
    vontade -- uma porta aberta que o CP3 nao pediu.
    """
    resposta = como_funcionario.post("/v1/empresas", json=NOVA)
    assert resposta.status_code == 403
    assert "ja pertence" in resposta.json()["detail"]


def test_sem_token_nao_cadastra(cliente):
    assert cliente.post("/v1/empresas", json=NOVA).status_code == 401


def test_consulta_de_codigo_livre_devolve_404(sem_empresa):
    """A tela de cadastro usa isto para avisar antes de enviar."""
    assert sem_empresa.get("/v1/empresas/nao-existe").status_code == 404


def test_consulta_nao_expoe_dado_de_consumo(sem_empresa):
    sem_empresa.post("/v1/empresas", json=NOVA)
    corpo = sem_empresa.get("/v1/empresas/padaria-central").json()
    assert set(corpo) <= {
        "codigo",
        "nome",
        "criado_por_uid",
        "criado_em",
        "atualizado_por_uid",
        "atualizado_em",
    }

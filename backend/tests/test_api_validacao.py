"""Validacao de entrada na borda da API.

O Pydantic recusa o corpo malformado antes de o handler rodar, entao
estes testes nao precisam de Firestore. E tambem a prova de que entrada
invalida nao chega ao banco -- exigencia do guia: "toda entrada e
validada (tipo, tamanho, formato) antes de chegar ao banco".
"""

import pytest

CONSUMO_VALIDO = {
    "unidade_id": "abc123",
    "competencia": "2026-01",
    "fonte_id": "eletricidade",
    "quantidade": "1500",
    "unidade_medida": "kWh",
}


def _com(**mudancas):
    corpo = dict(CONSUMO_VALIDO)
    corpo.update(mudancas)
    return corpo


# --------------------------------------------------------------------
# Quantidade: tipo
# --------------------------------------------------------------------


def test_quantidade_como_numero_decimal_e_recusada(como_funcionario):
    """O ponto central do CA-02.

    Um numero JSON ja chegou impreciso. Recusar aqui mostra ao front
    exatamente onde corrigir, em vez de gravar um valor contaminado.
    """
    resposta = como_funcionario.put("/v1/consumos", json=_com(quantidade=1500.5))
    assert resposta.status_code == 422
    assert "texto" in resposta.text.lower()


def test_quantidade_como_texto_e_aceita_pela_validacao(como_funcionario_sem_banco):
    """Passa da validacao e so entao falha por falta de banco.

    Qualquer coisa diferente de 422 prova que o formato foi aceito.
    """
    resposta = como_funcionario_sem_banco.put("/v1/consumos", json=_com(quantidade="1500.5"))
    assert resposta.status_code != 422


def test_quantidade_inteira_e_aceita(como_funcionario_sem_banco):
    resposta = como_funcionario_sem_banco.put("/v1/consumos", json=_com(quantidade=1500))
    assert resposta.status_code != 422


@pytest.mark.parametrize("valor", ["", "   ", "abc", "NaN", "Infinity", None, True, []])
def test_quantidade_invalida_e_recusada(como_funcionario, valor):
    resposta = como_funcionario.put("/v1/consumos", json=_com(quantidade=valor))
    assert resposta.status_code == 422


def test_quantidade_ausente_e_recusada(como_funcionario):
    corpo = dict(CONSUMO_VALIDO)
    del corpo["quantidade"]
    assert como_funcionario.put("/v1/consumos", json=corpo).status_code == 422


# --------------------------------------------------------------------
# Competencia
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "competencia",
    ["2026-1", "26-01", "2026/01", "2026-13", "2026-00", "2026", "", "marco"],
)
def test_competencia_malformada_e_recusada(como_funcionario, competencia):
    resposta = como_funcionario.put("/v1/consumos", json=_com(competencia=competencia))
    assert resposta.status_code == 422


def test_competencia_no_futuro_e_recusada(como_funcionario):
    resposta = como_funcionario.put("/v1/consumos", json=_com(competencia="2099-12"))
    assert resposta.status_code == 422
    assert "futuro" in resposta.text.lower()


def test_competencia_antes_do_catalogo_e_recusada(como_funcionario):
    resposta = como_funcionario.put("/v1/consumos", json=_com(competencia="2020-01"))
    assert resposta.status_code == 422


# --------------------------------------------------------------------
# Campos obrigatorios e tamanho
# --------------------------------------------------------------------


@pytest.mark.parametrize("campo", ["unidade_id", "fonte_id", "unidade_medida"])
def test_campo_obrigatorio_vazio_e_recusado(como_funcionario, campo):
    resposta = como_funcionario.put("/v1/consumos", json=_com(**{campo: ""}))
    assert resposta.status_code == 422


def test_unidade_de_medida_longa_demais_e_recusada(como_funcionario):
    resposta = como_funcionario.put(
        "/v1/consumos", json=_com(unidade_medida="quilowatt-hora-por-mes")
    )
    assert resposta.status_code == 422


# --------------------------------------------------------------------
# Unidade da rede
# --------------------------------------------------------------------


def test_uf_com_tamanho_errado_e_recusada(como_funcionario):
    resposta = como_funcionario.post(
        "/v1/unidades", json={"nome": "Loja", "cidade": "Brasilia", "uf": "DFF"}
    )
    assert resposta.status_code == 422


def test_uf_e_normalizada_para_maiuscula(como_funcionario_sem_banco):
    """Minuscula nao e erro: o sistema corrige em vez de reclamar."""
    resposta = como_funcionario_sem_banco.post(
        "/v1/unidades", json={"nome": "Loja", "cidade": "Brasilia", "uf": "df"}
    )
    assert resposta.status_code != 422


def test_nome_so_com_espaco_e_recusado(como_funcionario):
    resposta = como_funcionario.post(
        "/v1/unidades", json={"nome": "   ", "cidade": "Brasilia", "uf": "DF"}
    )
    assert resposta.status_code == 422


def test_nome_longo_demais_e_recusado(como_funcionario):
    resposta = como_funcionario.post(
        "/v1/unidades", json={"nome": "x" * 200, "cidade": "Brasilia", "uf": "DF"}
    )
    assert resposta.status_code == 422

"""Autoria dos registros -- CA-01 da issue #35.

Todo registro guarda quem gravou e quando. O caso que importa de
verdade e a correcao: o lancamento e gravado com `set`, que substitui o
documento inteiro, entao sem cuidado a primeira correcao apagaria a
autoria original.
"""

import pytest

pytestmark = pytest.mark.precisa_banco

UID_EMPRESA_A = "ana"
UID_EMPRESA_B = "bruno"
UID_COLEGA_A = "carlos"


def _criar_unidade(cliente, nome="Loja Asa Norte"):
    resposta = cliente.post(
        "/v1/unidades", json={"nome": nome, "cidade": "Brasilia", "uf": "DF"}
    )
    assert resposta.status_code == 201
    return resposta.json()


def _lancar(cliente, unidade_id, quantidade, competencia="2026-01"):
    resposta = cliente.put(
        "/v1/consumos",
        json={
            "unidade_id": unidade_id,
            "competencia": competencia,
            "fonte_id": "eletricidade",
            "quantidade": quantidade,
            "unidade_medida": "kWh",
        },
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


# --------------------------------------------------------------------
# Unidades
# --------------------------------------------------------------------


def test_unidade_guarda_quem_criou(como_funcionario):
    unidade = _criar_unidade(como_funcionario)
    assert unidade["criado_por_uid"] == UID_EMPRESA_A
    assert unidade["atualizado_por_uid"] == UID_EMPRESA_A


def test_data_de_criacao_e_iso_utc(como_funcionario):
    from datetime import datetime

    unidade = _criar_unidade(como_funcionario)
    instante = datetime.fromisoformat(unidade["criado_em"])
    assert instante.tzinfo is not None
    assert instante.utcoffset().total_seconds() == 0


def test_autoria_sobrevive_a_leitura(como_funcionario):
    criada = _criar_unidade(como_funcionario)
    lida = como_funcionario.get(f"/v1/unidades/{criada['id']}").json()
    assert lida["criado_por_uid"] == criada["criado_por_uid"]
    assert lida["criado_em"] == criada["criado_em"]


def test_autoria_enviada_pelo_cliente_e_descartada(como_funcionario):
    """O ponto da regra: autoria vem da claim, nao do corpo do pedido.

    Um campo que o cliente escolhe nao prova nada -- se bastasse mandar
    `criado_por_uid` no JSON, a auditoria registraria quem o cliente
    quisesse.
    """
    resposta = como_funcionario.post(
        "/v1/unidades",
        json={
            "nome": "Loja Falsa",
            "cidade": "Brasilia",
            "uf": "DF",
            "criado_por_uid": "fulano-inventado",
            "criado_em": "1999-01-01T00:00:00+00:00",
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["criado_por_uid"] == UID_EMPRESA_A
    assert not resposta.json()["criado_em"].startswith("1999")


# --------------------------------------------------------------------
# Consumos
# --------------------------------------------------------------------


def test_lancamento_guarda_quem_lancou(como_funcionario):
    unidade = _criar_unidade(como_funcionario)
    consumo = _lancar(como_funcionario, unidade["id"], "1500")
    assert consumo["criado_por_uid"] == UID_EMPRESA_A
    assert consumo["criado_em"] is not None


def test_correcao_preserva_quem_criou(como_funcionario, como_colega):
    """O caso que justifica o modulo inteiro.

    Como `set` substitui o documento, uma correcao sem cuidado apagaria
    `criado_por_uid` e o lancamento passaria a parecer criado por quem
    corrigiu -- perdendo exatamente o rastro que o CA-01 pede.

    A correcao tem de vir de OUTRA pessoa da mesma empresa. Com o mesmo
    usuario corrigindo o proprio lancamento, a igualdade valeria por
    coincidencia e o teste passaria mesmo com o bug.
    """
    unidade = _criar_unidade(como_funcionario)
    original = _lancar(como_funcionario, unidade["id"], "1500")
    assert original["criado_por_uid"] == UID_EMPRESA_A

    corrigido = _lancar(como_colega, unidade["id"], "1000")

    assert corrigido["criado_por_uid"] == UID_EMPRESA_A, "perdeu quem criou"
    assert corrigido["criado_em"] == original["criado_em"]
    assert corrigido["atualizado_por_uid"] == UID_COLEGA_A


def test_correcao_atualiza_a_data_de_alteracao(como_funcionario):
    unidade = _criar_unidade(como_funcionario)
    _lancar(como_funcionario, unidade["id"], "1500")
    corrigido = _lancar(como_funcionario, unidade["id"], "1000")

    assert corrigido["atualizado_em"] >= corrigido["criado_em"]
    assert corrigido["emissao_kg_co2e"] == "42.600"


def test_lancamento_antigo_sem_autoria_nao_quebra(como_funcionario, banco):
    """Dado gravado antes do CA-01 continua legivel.

    Devolver None e mais honesto que inventar um autor para um registro
    que nao tem um.
    """
    unidade = _criar_unidade(como_funcionario)
    consumo = _lancar(como_funcionario, unidade["id"], "1500")

    documento = (
        banco.collection("tenants")
        .document("empresa-a")
        .collection("consumos")
        .document(consumo["id"])
    )
    dados = documento.get().to_dict()
    for campo in ("criado_por_uid", "criado_em", "atualizado_por_uid", "atualizado_em"):
        dados.pop(campo, None)
    documento.set(dados)

    lido = como_funcionario.get(f"/v1/consumos/{consumo['id']}")
    assert lido.status_code == 200
    assert lido.json()["criado_por_uid"] is None
    assert lido.json()["emissao_kg_co2e"] == "63.900"

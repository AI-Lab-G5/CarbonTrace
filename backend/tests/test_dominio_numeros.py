"""Conversao de entrada externa em Decimal.

A regra do CA-02: quantidade trafega como texto. Float e recusado
porque um numero JSON ja chegou impreciso -- aceita-lo esconderia
onde a exatidao se perdeu.
"""

from decimal import Decimal

import pytest

from app.dominio.numeros import (
    ValorNaoDecimal,
    arredondar_emissao,
    como_texto,
    para_decimal,
)


def test_texto_simples():
    assert para_decimal("1500") == Decimal("1500")


def test_texto_com_fracao():
    assert para_decimal("350.5") == Decimal("350.5")


def test_texto_com_espaco_em_volta():
    assert para_decimal("  42  ") == Decimal("42")


def test_inteiro_e_aceito():
    """int nao perde exatidao, entao passa."""
    assert para_decimal(1500) == Decimal("1500")


def test_decimal_passa_direto():
    assert para_decimal(Decimal("0.0385")) == Decimal("0.0385")


def test_float_e_recusado():
    """O caso que motiva a regra toda."""
    with pytest.raises(ValorNaoDecimal, match="texto"):
        para_decimal(0.1)


def test_float_que_parece_inteiro_tambem_e_recusado():
    with pytest.raises(ValorNaoDecimal):
        para_decimal(1500.0)


def test_booleano_e_recusado():
    """bool e subclasse de int em Python.

    Sem este tratamento, True viraria quantidade 1 e um erro de
    digitacao no front viraria lancamento valido.
    """
    with pytest.raises(ValorNaoDecimal, match="booleano"):
        para_decimal(True)


def test_texto_vazio_e_recusado():
    with pytest.raises(ValorNaoDecimal, match="vazio"):
        para_decimal("")


def test_texto_so_com_espaco_e_recusado():
    with pytest.raises(ValorNaoDecimal, match="vazio"):
        para_decimal("   ")


def test_texto_nao_numerico_e_recusado():
    with pytest.raises(ValorNaoDecimal, match="nao e um numero"):
        para_decimal("mil e quinhentos")


def test_nan_e_recusado():
    """NaN e um Decimal valido e nao e uma quantidade."""
    with pytest.raises(ValorNaoDecimal, match="finito"):
        para_decimal("NaN")


def test_infinito_e_recusado():
    with pytest.raises(ValorNaoDecimal, match="finito"):
        para_decimal("Infinity")


def test_none_e_recusado():
    with pytest.raises(ValorNaoDecimal, match="tipo nao suportado"):
        para_decimal(None)


def test_lista_e_recusada():
    with pytest.raises(ValorNaoDecimal, match="tipo nao suportado"):
        para_decimal([1, 2])


def test_exatidao_preservada_onde_float_falharia():
    """0.1 + 0.2 em float da 0.30000000000000004."""
    soma = para_decimal("0.1") + para_decimal("0.2")
    assert soma == Decimal("0.3")
    assert soma != Decimal(str(0.1 + 0.2))


def test_texto_sem_notacao_cientifica():
    """str(Decimal) usa notacao cientifica em alguns casos.

    "1E+3" chegaria ao front como texto que ele nao sabe ler.
    """
    assert como_texto(Decimal("1E+3")) == "1000"
    assert como_texto(Decimal("0.0385")) == "0.0385"


def test_arredondamento_mantem_tres_casas():
    assert como_texto(arredondar_emissao(Decimal("57.75"))) == "57.750"

"""EP/BVA do motor de calculo: zero, negativo, teto, unidade e mes.

Classes de equivalencia e valores de fronteira dos criterios CA-02 e
CA-04. Funcoes puras, sem Firestore -- rodam em qualquer maquina e no CI
sem emulador.
"""

from decimal import Decimal

import pytest

from app.dominio.calculo import FatorAplicado, calcular, mediana, recalcular, somar
from app.dominio.erros import (
    QuantidadeAcimaDoTeto,
    QuantidadeInvalida,
    UnidadeIncompativel,
)

ELETRICIDADE_V1 = FatorAplicado(
    fonte_id="eletricidade",
    versao="v1",
    valor=Decimal("0.0385"),
    unidade_base="kWh",
    escopo="2",
    teto=Decimal("1000000"),
)

ELETRICIDADE_V2 = FatorAplicado(
    fonte_id="eletricidade",
    versao="v2",
    valor=Decimal("0.0426"),
    unidade_base="kWh",
    escopo="2",
    teto=Decimal("1000000"),
)

DIESEL_V1 = FatorAplicado(
    fonte_id="diesel",
    versao="v1",
    valor=Decimal("2.6"),
    unidade_base="L",
    escopo="1",
    teto=Decimal("200000"),
)


# --------------------------------------------------------------------
# Particao: quantidade valida
# --------------------------------------------------------------------


def test_calculo_de_eletricidade_em_kwh():
    """1500 kWh x 0,0385 = 57,750 kgCO2e (conferido a mao)."""
    r = calcular(Decimal("1500"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("57.750")


def test_calculo_de_diesel_com_fracao():
    """350,5 L x 2,6 = 911,300 kgCO2e (conferido a mao)."""
    r = calcular(Decimal("350.5"), "L", DIESEL_V1)
    assert r.emissao_kg_co2e == Decimal("911.300")


def test_resultado_guarda_a_versao_e_o_valor_do_fator():
    r = calcular(Decimal("1000"), "kWh", ELETRICIDADE_V1)
    assert r.fator_versao == "v1"
    assert r.fator_valor == Decimal("0.0385")


# --------------------------------------------------------------------
# Fronteira: zero
# --------------------------------------------------------------------


def test_zero_e_aceito():
    """Zero e um lancamento valido, e emite zero.

    "A loja nao consumiu diesel em marco" precisa poder ser registrado:
    e o que distingue um inventario completo de um com lacuna. Recusar
    zero obrigaria a escolher entre inventar um numero e deixar o mes
    em branco.
    """
    r = calcular(Decimal("0"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("0.000")
    assert r.quantidade_informada == Decimal("0")
    assert r.fator_versao == "v1"


def test_zero_nao_desaparece_na_serializacao():
    """Zero tem de sair como "0.000", nao como "0" nem como "0E-3"."""
    from app.dominio.numeros import como_texto

    r = calcular(Decimal("0"), "kWh", ELETRICIDADE_V1)
    assert como_texto(r.emissao_kg_co2e) == "0.000"


def test_logo_acima_de_zero_passa():
    """Fronteira inferior: o menor valor positivo e aceito."""
    r = calcular(Decimal("0.000001"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("0.000")


# --------------------------------------------------------------------
# Particao: quantidade negativa
# --------------------------------------------------------------------


def test_negativo_e_recusado():
    with pytest.raises(QuantidadeInvalida):
        calcular(Decimal("-1"), "kWh", ELETRICIDADE_V1)


def test_negativo_grande_e_recusado():
    with pytest.raises(QuantidadeInvalida):
        calcular(Decimal("-999999"), "kWh", ELETRICIDADE_V1)


# --------------------------------------------------------------------
# Fronteira: teto
# --------------------------------------------------------------------


def test_logo_abaixo_do_teto_passa():
    r = calcular(Decimal("999999"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e > 0


def test_exatamente_no_teto_passa():
    """O teto e inclusivo: 1.000.000 kWh e o ultimo valor aceito."""
    r = calcular(Decimal("1000000"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("38500.000")


def test_logo_acima_do_teto_e_recusado():
    with pytest.raises(QuantidadeAcimaDoTeto):
        calcular(Decimal("1000001"), "kWh", ELETRICIDADE_V1)


def test_teto_e_conferido_depois_da_conversao():
    """1001 MWh viram 1.001.000 kWh e estouram o teto.

    Se o teto fosse conferido antes da conversao, 1001 passaria --
    e o lancamento entraria mil vezes maior que o permitido.
    """
    with pytest.raises(QuantidadeAcimaDoTeto):
        calcular(Decimal("1001"), "MWh", ELETRICIDADE_V1)


# --------------------------------------------------------------------
# Particao: unidade
# --------------------------------------------------------------------


def test_mwh_converte_para_kwh():
    """2,5 MWh = 2500 kWh x 0,0385 = 96,250 kgCO2e (conferido a mao)."""
    r = calcular(Decimal("2.5"), "MWh", ELETRICIDADE_V1)
    assert r.quantidade_convertida == Decimal("2500.0")
    assert r.emissao_kg_co2e == Decimal("96.250")


def test_unidade_desconhecida_e_recusada():
    with pytest.raises(UnidadeIncompativel):
        calcular(Decimal("100"), "galao", ELETRICIDADE_V1)


def test_unidade_de_outra_fonte_e_recusada():
    """Litro nao serve para eletricidade.

    E a falha mais provavel na operacao: quem lanca varias fontes
    seguidas erra o seletor e manda a unidade da fonte anterior.
    """
    with pytest.raises(UnidadeIncompativel):
        calcular(Decimal("100"), "L", ELETRICIDADE_V1)


def test_mwh_nao_serve_para_diesel():
    with pytest.raises(UnidadeIncompativel):
        calcular(Decimal("100"), "MWh", DIESEL_V1)


# --------------------------------------------------------------------
# Arredondamento: ROUND_HALF_EVEN
# --------------------------------------------------------------------


def test_empate_arredonda_para_o_par_para_baixo():
    """1 kWh x 0,0385 = 0,0385 -> 0,038.

    Empate exato na quarta casa. Meio-para-o-par olha o digito anterior:
    8 e par, entao mantem. Com ROUND_HALF_UP daria 0,039.
    """
    r = calcular(Decimal("1"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("0.038")


def test_empate_arredonda_para_o_par_para_cima():
    """3 kWh x 0,0385 = 0,1155 -> 0,116.

    Mesmo empate, digito anterior 5 e impar, entao sobe. O par dos dois
    testes mostra que a regra nao e "sempre para baixo"."""
    r = calcular(Decimal("3"), "kWh", ELETRICIDADE_V1)
    assert r.emissao_kg_co2e == Decimal("0.116")


def test_arredondamento_vem_depois_da_multiplicacao():
    """Arredondar antes acumularia erro proporcional ao consumo."""
    r = calcular(Decimal("123456.789"), "kWh", ELETRICIDADE_V1)
    esperado = (Decimal("123456.789") * Decimal("0.0385")).quantize(Decimal("0.001"))
    assert r.emissao_kg_co2e == esperado


# --------------------------------------------------------------------
# CA-03: reprodutibilidade
# --------------------------------------------------------------------


def test_mesma_entrada_e_mesmo_fator_dao_o_mesmo_resultado():
    primeiro = calcular(Decimal("1234.56"), "kWh", ELETRICIDADE_V1)
    for _ in range(50):
        assert calcular(Decimal("1234.56"), "kWh", ELETRICIDADE_V1) == primeiro


def test_recalculo_com_o_fator_original_mantem_o_resultado():
    original = calcular(Decimal("1500"), "kWh", ELETRICIDADE_V1)
    refeito = recalcular(original, ELETRICIDADE_V1)
    assert refeito.emissao_kg_co2e == original.emissao_kg_co2e


def test_versao_nova_nao_altera_resultado_anterior():
    """Publicar a v2 nao mexe no que a v1 calculou.

    O coracao do CA-03: o lancamento guardou v1, e refazer a conta com
    v1 devolve o mesmo numero, mesmo com a v2 disponivel."""
    com_v1 = calcular(Decimal("1500"), "kWh", ELETRICIDADE_V1)
    com_v2 = calcular(Decimal("1500"), "kWh", ELETRICIDADE_V2)

    assert com_v1.emissao_kg_co2e == Decimal("57.750")
    assert com_v2.emissao_kg_co2e == Decimal("63.900")
    assert recalcular(com_v1, ELETRICIDADE_V1).emissao_kg_co2e == Decimal("57.750")


def test_recalculo_recusa_fator_de_outra_versao():
    original = calcular(Decimal("1500"), "kWh", ELETRICIDADE_V1)
    with pytest.raises(ValueError, match="fator original"):
        recalcular(original, ELETRICIDADE_V2)


# --------------------------------------------------------------------
# Agregacao
# --------------------------------------------------------------------


def test_soma_de_emissoes():
    assert somar([Decimal("10.001"), Decimal("20.002")]) == Decimal("30.003")


def test_soma_de_lista_vazia():
    assert somar([]) == Decimal("0.000")


def test_mediana_com_quantidade_impar():
    assert mediana([Decimal("10"), Decimal("30"), Decimal("20")]) == Decimal("20.000")


def test_mediana_com_quantidade_par():
    assert mediana([Decimal("10"), Decimal("20")]) == Decimal("15.000")


def test_mediana_resiste_a_unidade_atipica():
    """Tres lojas e um centro de distribuicao.

    A media daria 2575 e nenhuma loja se pareceria com ela. A mediana
    fica em 100 e descreve a rede de verdade.
    """
    valores = [Decimal("100"), Decimal("100"), Decimal("100"), Decimal("10000")]
    assert mediana(valores) == Decimal("100.000")
    assert somar(valores) == Decimal("10300.000")


def test_mediana_de_lista_vazia():
    assert mediana([]) == Decimal("0.000")

"""Calculo de emissoes e consolidacao. Funcoes puras, sem Firestore."""

import pytest

from app.models import Fator
from app.services.calculo import calcular_emissao, consolidar, desvio_da_mediana

FATOR_ENERGIA = Fator(
    fonte_id="energia_eletrica_sin",
    nome="Energia eletrica (SIN)",
    escopo="2",
    unidade_medida="kWh",
    kg_co2e_por_unidade=0.0385,
    fonte_referencia="MCTI - Fatores medios do SIN",
)


def test_calculo_simples():
    assert calcular_emissao(1000, FATOR_ENERGIA) == 38.5


def test_quantidade_zero_gera_emissao_zero():
    assert calcular_emissao(0, FATOR_ENERGIA) == 0.0


def test_quantidade_negativa_e_rejeitada():
    with pytest.raises(ValueError):
        calcular_emissao(-1, FATOR_ENERGIA)


def test_mesmo_fator_devolve_sempre_o_mesmo_resultado():
    """Determinismo: e a promessa central do produto.

    Recalcular um periodo com o fator da epoca tem de devolver o numero
    identico, ou a trilha de auditoria perde o sentido.
    """
    primeira = calcular_emissao(1234.56, FATOR_ENERGIA)
    for _ in range(100):
        assert calcular_emissao(1234.56, FATOR_ENERGIA) == primeira


def test_consolidacao_usa_mediana_e_nao_media():
    """Com uma unidade atipica, mediana e media divergem.

    Tres lojas pequenas e um centro de distribuicao enorme: a media sobe
    para perto de 2600 e nenhuma loja se parece com ela. A mediana fica
    em 100 e descreve a rede de verdade.
    """
    emissoes = {"loja_a": 100.0, "loja_b": 100.0, "loja_c": 100.0, "cd": 10000.0}
    total, mediana = consolidar(emissoes)
    assert total == 10300.0
    assert mediana == 100.0


def test_consolidacao_de_rede_vazia():
    assert consolidar({}) == (0.0, 0.0)


def test_desvio_percentual_da_mediana():
    assert desvio_da_mediana(150.0, 100.0) == 50.0
    assert desvio_da_mediana(50.0, 100.0) == -50.0


def test_desvio_com_mediana_zero_nao_divide_por_zero():
    assert desvio_da_mediana(10.0, 0.0) is None

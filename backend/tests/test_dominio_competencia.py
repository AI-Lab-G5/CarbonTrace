"""EP/BVA da competencia: o "mes" do criterio CA-04.

Formato AAAA-MM, com piso no inicio do catalogo e teto no mes corrente.
A data de referencia entra como parametro para que os testes de fronteira
nao quebrem quando o calendario virar.
"""

from datetime import date

import pytest

from app.dominio.competencia import COMPETENCIA_MINIMA, hoje_competencia, validar
from app.dominio.erros import CompetenciaInvalida

HOJE = date(2026, 10, 27)


# --------------------------------------------------------------------
# Particao: formato
# --------------------------------------------------------------------


def test_formato_valido():
    assert validar("2026-03", referencia=HOJE) == "2026-03"


def test_espaco_em_volta_e_tolerado():
    assert validar("  2026-03  ", referencia=HOJE) == "2026-03"


@pytest.mark.parametrize(
    "entrada",
    [
        "2026-3",      # mes sem zero a esquerda
        "26-03",       # ano com dois digitos
        "2026/03",     # separador errado
        "03-2026",     # ordem invertida
        "2026-03-15",  # data completa
        "marco/2026",  # por extenso
        "",
        "2026",
    ],
)
def test_formatos_invalidos(entrada: str):
    with pytest.raises(CompetenciaInvalida, match="formato"):
        validar(entrada, referencia=HOJE)


def test_nao_texto_e_recusado():
    with pytest.raises(CompetenciaInvalida, match="texto"):
        validar(202603, referencia=HOJE)  # type: ignore[arg-type]


# --------------------------------------------------------------------
# Fronteira: mes 00 e mes 13
# --------------------------------------------------------------------


def test_mes_zero_e_recusado():
    with pytest.raises(CompetenciaInvalida):
        validar("2026-00", referencia=HOJE)


def test_mes_treze_e_recusado():
    with pytest.raises(CompetenciaInvalida):
        validar("2026-13", referencia=HOJE)


def test_janeiro_e_dezembro_passam():
    assert validar("2026-01", referencia=HOJE) == "2026-01"
    assert validar("2025-12", referencia=HOJE) == "2025-12"


# --------------------------------------------------------------------
# Fronteira: piso do catalogo
# --------------------------------------------------------------------


def test_exatamente_no_piso_passa():
    assert validar(COMPETENCIA_MINIMA, referencia=HOJE) == COMPETENCIA_MINIMA


def test_logo_abaixo_do_piso_e_recusado():
    with pytest.raises(CompetenciaInvalida, match="anterior"):
        validar("2024-12", referencia=HOJE)


# --------------------------------------------------------------------
# Fronteira: teto no mes corrente
# --------------------------------------------------------------------


def test_mes_corrente_passa():
    """Quem fecha o mes dia 28 nao deveria esperar ate dia 1."""
    assert validar("2026-10", referencia=HOJE) == "2026-10"


def test_mes_anterior_passa():
    assert validar("2026-09", referencia=HOJE) == "2026-09"


def test_mes_seguinte_e_recusado():
    with pytest.raises(CompetenciaInvalida, match="futuro"):
        validar("2026-11", referencia=HOJE)


def test_ano_seguinte_e_recusado():
    with pytest.raises(CompetenciaInvalida, match="futuro"):
        validar("2027-01", referencia=HOJE)


def test_virada_de_ano_em_dezembro():
    """Fronteira do calendario: em dezembro, janeiro ainda e futuro."""
    dezembro = date(2026, 12, 15)
    assert validar("2026-12", referencia=dezembro) == "2026-12"
    with pytest.raises(CompetenciaInvalida, match="futuro"):
        validar("2027-01", referencia=dezembro)


def test_competencia_de_hoje_sem_referencia_explicita():
    """Sem parametro, usa a data real -- e precisa aceitar o mes atual."""
    assert validar(hoje_competencia()) == hoje_competencia()

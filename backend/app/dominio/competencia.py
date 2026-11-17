"""Competencia: o mes de referencia de um lancamento.

Formato AAAA-MM. Escolhido por ordenar corretamente como texto, o que
permite comparar e filtrar no Firestore sem converter nada.
"""

import re
from datetime import date

from app.dominio.erros import CompetenciaInvalida

_FORMATO = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")

# Piso: antes disso nao existe fator publicado, entao nenhum lancamento
# poderia ser calculado de qualquer forma.
COMPETENCIA_MINIMA = "2025-01"


def hoje_competencia(referencia: date | None = None) -> str:
    """Competencia do mes corrente."""
    hoje = referencia or date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"


def validar(competencia: str, *, referencia: date | None = None) -> str:
    """Valida formato e intervalo, devolvendo a competencia normalizada.

    O teto e o mes corrente: nao se lanca consumo de um mes que ainda
    nao terminou de acontecer. Lancamento do mes vigente e permitido --
    quem fecha o mes dia 28 nao deveria esperar ate dia 1.
    """
    if not isinstance(competencia, str):
        raise CompetenciaInvalida("Competencia deve ser texto no formato AAAA-MM.")

    texto = competencia.strip()

    if not _FORMATO.match(texto):
        raise CompetenciaInvalida(
            f"Competencia {competencia!r} invalida. Use o formato AAAA-MM, "
            "com mes entre 01 e 12."
        )

    if texto < COMPETENCIA_MINIMA:
        raise CompetenciaInvalida(
            f"Competencia {texto} anterior a {COMPETENCIA_MINIMA}, quando "
            "comeca o catalogo de fatores."
        )

    limite = hoje_competencia(referencia)
    if texto > limite:
        raise CompetenciaInvalida(
            f"Competencia {texto} esta no futuro. O limite e {limite}."
        )

    return texto

"""Conversao de unidades antes do calculo.

Eletricidade aceita kWh e MWh porque a conta de luz de uma loja pequena
vem em kWh e a de um centro de distribuicao vem em MWh. As demais fontes
tem unidade unica: diesel e gasolina em litro, GLP em quilograma.

Aceitar a unidade errada em silencio seria a falha mais cara do sistema --
informar 1000 em MWh onde se esperava kWh produz um numero mil vezes maior
sem nenhum sinal de erro. Por isso a conversao e explicita e qualquer
unidade nao prevista e recusada.
"""

from decimal import Decimal

from app.dominio.erros import UnidadeIncompativel

# Fator de conversao de cada unidade aceita para a unidade base da fonte.
# A chave e (unidade informada, unidade base do fator).
_CONVERSOES: dict[tuple[str, str], Decimal] = {
    ("kWh", "kWh"): Decimal(1),
    ("MWh", "kWh"): Decimal(1000),
    ("L", "L"): Decimal(1),
    ("kg", "kg"): Decimal(1),
}


def unidades_aceitas(unidade_base: str) -> list[str]:
    """Unidades que podem ser informadas para um fator nesta unidade base."""
    return sorted(
        informada for (informada, base) in _CONVERSOES if base == unidade_base
    )


def converter(
    quantidade: Decimal,
    unidade_informada: str,
    unidade_base: str,
) -> Decimal:
    """Converte a quantidade para a unidade em que o fator foi publicado.

    Devolve a quantidade intocada quando as unidades ja coincidem, para
    que o caso comum nao passe por multiplicacao nenhuma.
    """
    chave = (unidade_informada, unidade_base)
    fator = _CONVERSOES.get(chave)

    if fator is None:
        raise UnidadeIncompativel(
            unidade_informada=unidade_informada,
            unidade_base=unidade_base,
            aceitas=unidades_aceitas(unidade_base),
        )

    if fator == 1:
        return quantidade
    return quantidade * fator

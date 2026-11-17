"""Numeros do dominio: Decimal do inicio ao fim.

Por que nao float: 0.1 + 0.2 nao da 0.3 em binario. Num inventario que se
vende como auditavel, dois recalculos do mesmo periodo precisam devolver
exatamente o mesmo numero -- e float nao garante isso quando os valores
mudam de ordem de grandeza ou de ordem de soma.

Decisoes registradas em ADR-009:
  - ROUND_HALF_EVEN (meio para o par), decidido pelo time em 25/10.
  - Resultado quantizado em 3 casas, ou seja, grama de CO2e.
"""

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

# Precisao do resultado de emissao: 3 casas = 1 grama de CO2e.
# Mais casas nao acrescentam informacao -- nenhum fator de emissao
# publicado tem exatidao melhor que isso.
CASAS_EMISSAO = Decimal("0.001")

# Precisao da quantidade aceita na entrada. Seis casas cobrem desde
# litros com fracao ate kWh sem perder nada que um medidor registre.
CASAS_QUANTIDADE = Decimal("0.000001")


class ValorNaoDecimal(ValueError):
    """Entrada que nao pode virar Decimal com seguranca."""


def para_decimal(valor: object, *, campo: str = "valor") -> Decimal:
    """Converte entrada externa em Decimal, recusando float.

    Float e recusado de proposito. Um numero JSON que chega como 0.1
    ja perdeu exatidao antes de tocar neste codigo, e aceita-lo aqui
    esconderia o problema em vez de apontar onde ele comecou. O
    contrato com o front e: quantidade trafega como string.
    """
    if isinstance(valor, Decimal):
        return valor

    if isinstance(valor, bool):
        # bool e subclasse de int em Python; aceitar True como 1 seria
        # transformar um erro de digitacao em lancamento valido.
        raise ValorNaoDecimal(f"{campo} nao aceita booleano.")

    if isinstance(valor, float):
        raise ValorNaoDecimal(
            f"{campo} deve vir como texto, nao como numero decimal. "
            f'Envie "{valor}" entre aspas para preservar a exatidao.'
        )

    if isinstance(valor, int):
        return Decimal(valor)

    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            raise ValorNaoDecimal(f"{campo} nao pode ser vazio.")
        try:
            convertido = Decimal(texto)
        except InvalidOperation as erro:
            raise ValorNaoDecimal(f"{campo} nao e um numero: {valor!r}.") from erro
        if not convertido.is_finite():
            # NaN e Infinity sao Decimal validos e nao sao quantidades.
            raise ValorNaoDecimal(f"{campo} precisa ser um numero finito.")
        return convertido

    raise ValorNaoDecimal(f"{campo} tem tipo nao suportado: {type(valor).__name__}.")


def arredondar_emissao(valor: Decimal) -> Decimal:
    """Quantiza o resultado da emissao com a regra acordada."""
    return valor.quantize(CASAS_EMISSAO, rounding=ROUND_HALF_EVEN)


def arredondar_quantidade(valor: Decimal) -> Decimal:
    """Quantiza a quantidade informada."""
    return valor.quantize(CASAS_QUANTIDADE, rounding=ROUND_HALF_EVEN)


def como_texto(valor: Decimal) -> str:
    """Serializa Decimal sem notacao cientifica.

    str(Decimal("1E+3")) devolve "1E+3", que o front nao sabe ler.
    O 'f' no format forca a forma posicional.
    """
    return format(valor, "f")

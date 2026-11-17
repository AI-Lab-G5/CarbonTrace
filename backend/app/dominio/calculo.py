"""Motor de calculo de emissoes.

Funcoes puras: entram valores, sai valor. Nao tocam no Firestore, nao
sabem o que e uma requisicao HTTP. E o que permite conferir cada exemplo
a mao e repetir o calculo de um periodo antigo com o fator da epoca.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.dominio.erros import QuantidadeAcimaDoTeto, QuantidadeInvalida
from app.dominio.numeros import arredondar_emissao
from app.dominio.unidades import converter


@dataclass(frozen=True)
class FatorAplicado:
    """O fator exatamente como foi usado num calculo.

    Congelado de proposito: uma vez aplicado, o fator daquele lancamento
    nao muda nunca mais, mesmo que uma versao nova seja publicada.
    """

    fonte_id: str
    versao: str
    valor: Decimal
    unidade_base: str
    escopo: str
    teto: Decimal


@dataclass(frozen=True)
class Resultado:
    """Resultado de um calculo, com tudo que o reproduz."""

    quantidade_informada: Decimal
    unidade_informada: str
    quantidade_convertida: Decimal
    unidade_base: str
    fator_versao: str
    fator_valor: Decimal
    emissao_kg_co2e: Decimal
    escopo: str


def calcular(
    quantidade: Decimal,
    unidade_informada: str,
    fator: FatorAplicado,
) -> Resultado:
    """Converte a quantidade e multiplica pelo fator.

    A ordem importa: converte primeiro, multiplica depois, arredonda por
    ultimo. Arredondar antes da multiplicacao introduziria um erro que
    cresce com a magnitude do consumo.
    """
    if quantidade < 0:
        raise QuantidadeInvalida(
            "Quantidade nao pode ser negativa. Para corrigir um lancamento "
            "a maior, envie o valor correto -- o registro e sobrescrito."
        )

    # Zero e aceito, e de proposito (CA-03 da issue #11). "A loja nao
    # consumiu diesel em marco" e uma afirmacao diferente de "ninguem
    # lancou diesel em marco": a primeira fecha o inventario, a segunda
    # deixa um buraco. Recusar zero obrigaria o usuario a escolher entre
    # mentir e deixar a lacuna.
    convertida = converter(quantidade, unidade_informada, fator.unidade_base)

    # O teto e conferido depois da conversao, na unidade base. Assim um
    # valor em MWh e comparado com o mesmo teto que um valor em kWh.
    if convertida > fator.teto:
        raise QuantidadeAcimaDoTeto(
            quantidade=convertida,
            teto=fator.teto,
            unidade=fator.unidade_base,
        )

    emissao = arredondar_emissao(convertida * fator.valor)

    return Resultado(
        quantidade_informada=quantidade,
        unidade_informada=unidade_informada,
        quantidade_convertida=convertida,
        unidade_base=fator.unidade_base,
        fator_versao=fator.versao,
        fator_valor=fator.valor,
        emissao_kg_co2e=emissao,
        escopo=fator.escopo,
    )


def recalcular(resultado: Resultado, fator: FatorAplicado) -> Resultado:
    """Refaz um calculo com o fator original.

    Existe para a prova do CA-03: dado um resultado guardado e o fator
    que ele registrou, repetir a conta devolve o mesmo numero. Usado
    nos testes e disponivel para auditoria.
    """
    if fator.versao != resultado.fator_versao:
        raise ValueError(
            f"Recalculo exige o fator original (versao {resultado.fator_versao}), "
            f"recebido {fator.versao}."
        )
    return calcular(
        resultado.quantidade_informada,
        resultado.unidade_informada,
        fator,
    )


def somar(emissoes: list[Decimal]) -> Decimal:
    """Soma emissoes ja arredondadas.

    Soma dos arredondados, e nao arredondamento da soma: cada lancamento
    e um numero publicado, e o total precisa bater com a conferencia item
    a item que um auditor faria na planilha.
    """
    total = sum(emissoes, start=Decimal(0))
    return arredondar_emissao(total)


def mediana(emissoes: list[Decimal]) -> Decimal:
    """Mediana das emissoes por unidade.

    Mediana e nao media: um centro de distribuicao grande puxa a media
    para cima e nenhuma loja se parece com ela. A mediana descreve a
    rede de verdade.
    """
    if not emissoes:
        return Decimal("0.000")

    ordenadas = sorted(emissoes)
    meio = len(ordenadas) // 2

    if len(ordenadas) % 2 == 1:
        return arredondar_emissao(ordenadas[meio])

    return arredondar_emissao((ordenadas[meio - 1] + ordenadas[meio]) / 2)

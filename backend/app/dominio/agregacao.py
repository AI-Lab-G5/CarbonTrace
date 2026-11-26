"""Agregacao de lancamentos em totais por unidade, regiao, mes e escopo.

Entrega da Jornada 4 (issue #35). Como o resto de `dominio/`, nao conhece
FastAPI nem Firestore: recebe lancamentos, devolve totais.

Por que a igualdade e exata
---------------------------
O CA-04 exige que a soma por unidade, a soma por regiao e o total geral
sejam iguais -- nao aproximadamente iguais. Isso sai de graca de duas
decisoes ja tomadas no CP2, desde que nao sejam desfeitas aqui:

1. Toda emissao gravada ja esta arredondada em 3 casas (ADR-009). Somar
   numeros de 3 casas da um numero de 3 casas, sem erro nenhum.
2. Nao se arredonda de novo no agregado. Reagrupar e somar outra vez e a
   mesma conta em outra ordem, e `Decimal` e exato na adicao -- ao
   contrario de float, em que (a+b)+c pode diferir de a+(b+c).

Reagrupar nao muda a soma; arredondar de novo mudaria. Por isso
`agregar` soma e nao arredonda, e ha teste fixando os tres totais.

Regiao
------
Regiao = UF da unidade. A definicao e do Tech Lead (#34); enquanto ela
nao vem, a UF e o unico recorte que ja existe no cadastro e nao exige
migrar unidade nenhuma. Trocar depois mexe so em quem monta o
`Lancamento`, nao neste modulo.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.dominio.calculo import mediana as mediana_de
from app.dominio.numeros import CASAS_EMISSAO

# CA-06: alerta so acima de 50% em valor absoluto. Exatamente +/-50% NAO
# alerta -- a comparacao e estritamente maior, nao maior ou igual.
LIMIAR_ALERTA_PERCENTUAL = Decimal("50")

# CA-06: abaixo disso a mediana nao descreve nada, e comparar vira ruido.
MINIMO_ELEGIVEIS = 3

SEM_ELEGIVEIS = "Menos de 3 unidades elegiveis na competencia."
MEDIANA_ZERO = "Mediana zero ou negativa: nao ha base de comparacao."


@dataclass(frozen=True)
class Lancamento:
    """Um consumo ja calculado, com o que a agregacao precisa saber.

    Montado por quem le o banco. O dominio nao vai atras de nome de
    unidade nem de UF -- recebe tudo pronto e so soma.
    """

    unidade_id: str
    unidade_nome: str
    regiao: str
    fonte_id: str
    escopo: str
    emissao_kg_co2e: Decimal
    unidade_ativa: bool = True


@dataclass(frozen=True)
class TotalUnidade:
    unidade_id: str
    unidade_nome: str
    regiao: str
    emissao_kg_co2e: Decimal
    fontes_lancadas: int
    unidade_ativa: bool


@dataclass(frozen=True)
class TotalRegiao:
    regiao: str
    emissao_kg_co2e: Decimal
    unidades: int


@dataclass(frozen=True)
class TotalEscopo:
    escopo: str
    emissao_kg_co2e: Decimal


@dataclass(frozen=True)
class Agregado:
    """Os totais de uma competencia, em todos os recortes pedidos."""

    competencia: str
    total_kg_co2e: Decimal
    por_unidade: tuple[TotalUnidade, ...]
    por_regiao: tuple[TotalRegiao, ...]
    por_escopo: tuple[TotalEscopo, ...]


@dataclass(frozen=True)
class LinhaComparacao:
    unidade_id: str
    unidade_nome: str
    emissao_kg_co2e: Decimal
    desvio_percentual: Decimal
    alerta: bool


@dataclass(frozen=True)
class Comparacao:
    """Ranking e desvio contra a mediana (CA-06, CT-M12).

    `disponivel=False` nao e erro: e a resposta correta quando a rede
    nao tem base de comparacao. O motivo vai junto para a tela poder
    dizer por que, em vez de mostrar um ranking vazio.
    """

    disponivel: bool
    motivo: str | None
    mediana_kg_co2e: Decimal
    linhas: tuple[LinhaComparacao, ...]


class EmissaoNaoArredondada(ValueError):
    """Um lancamento chegou com mais casas do que o contrato permite."""


def _conferir_escala(valor: Decimal, unidade_id: str) -> None:
    """Recusa emissao fora das 3 casas.

    A igualdade exata do CA-04 depende de toda parcela ter a mesma
    escala. Se um lancamento chegasse com 6 casas, os totais por recorte
    passariam a divergir no sexto digito e ninguem veria -- ate um
    auditor somar a planilha. Falhar aqui, alto, custa menos.
    """
    if valor != valor.quantize(CASAS_EMISSAO):
        raise EmissaoNaoArredondada(
            f"Emissao de {unidade_id} tem mais de 3 casas: {valor}. "
            "Todo lancamento e arredondado no calculo (ADR-009); um valor "
            "assim indica gravacao fora do motor."
        )


def agregar(lancamentos: list[Lancamento], competencia: str) -> Agregado:
    """Soma os lancamentos nos tres recortes, sem arredondar de novo.

    Unidades vem ordenadas por emissao decrescente e, no empate, por id
    crescente -- a mesma ordem do CA-06, para que a tela e o ranking nao
    discordem. Regioes e escopos vem em ordem alfabetica, que e estavel
    e nao sugere ranking onde nao ha.
    """
    unidades: dict[str, dict] = {}
    regioes: dict[str, Decimal] = {}
    unidades_por_regiao: dict[str, set[str]] = {}
    escopos: dict[str, Decimal] = {}
    total = Decimal(0)

    for lancamento in lancamentos:
        _conferir_escala(lancamento.emissao_kg_co2e, lancamento.unidade_id)
        emissao = lancamento.emissao_kg_co2e

        atual = unidades.setdefault(
            lancamento.unidade_id,
            {
                "nome": lancamento.unidade_nome,
                "regiao": lancamento.regiao,
                "emissao": Decimal(0),
                "fontes": set(),
                "ativa": lancamento.unidade_ativa,
            },
        )
        atual["emissao"] += emissao
        atual["fontes"].add(lancamento.fonte_id)

        regioes[lancamento.regiao] = regioes.get(lancamento.regiao, Decimal(0)) + emissao
        unidades_por_regiao.setdefault(lancamento.regiao, set()).add(
            lancamento.unidade_id
        )
        escopos[lancamento.escopo] = escopos.get(lancamento.escopo, Decimal(0)) + emissao
        total += emissao

    por_unidade = tuple(
        sorted(
            (
                TotalUnidade(
                    unidade_id=uid,
                    unidade_nome=dados["nome"],
                    regiao=dados["regiao"],
                    emissao_kg_co2e=dados["emissao"],
                    fontes_lancadas=len(dados["fontes"]),
                    unidade_ativa=dados["ativa"],
                )
                for uid, dados in unidades.items()
            ),
            key=lambda t: (-t.emissao_kg_co2e, t.unidade_id),
        )
    )

    por_regiao = tuple(
        TotalRegiao(
            regiao=nome,
            emissao_kg_co2e=valor,
            unidades=len(unidades_por_regiao[nome]),
        )
        for nome, valor in sorted(regioes.items())
    )

    por_escopo = tuple(
        TotalEscopo(escopo=nome, emissao_kg_co2e=valor)
        for nome, valor in sorted(escopos.items())
    )

    return Agregado(
        competencia=competencia,
        total_kg_co2e=total,
        por_unidade=por_unidade,
        por_regiao=por_regiao,
        por_escopo=por_escopo,
    )


def comparar(elegiveis: list[TotalUnidade]) -> Comparacao:
    """Ranking e desvio contra a mediana, pelas regras do CA-06.

    Quem decide a elegibilidade e o chamador, porque ela depende de
    cadastro (unidade ativa, fonte esperada, coleta completa) e nao de
    aritmetica. Aqui ficam so os limiares, que sao a parte que tem de
    estar fixada em teste.

    Mediana e nao media, pelo mesmo motivo do consolidado: um centro de
    distribuicao puxaria a media e faria toda loja parecer pequena.
    """
    if len(elegiveis) < MINIMO_ELEGIVEIS:
        return Comparacao(
            disponivel=False,
            motivo=SEM_ELEGIVEIS,
            mediana_kg_co2e=Decimal("0.000"),
            linhas=(),
        )

    valores = [u.emissao_kg_co2e for u in elegiveis]
    centro = mediana_de(valores)

    if centro <= 0:
        return Comparacao(
            disponivel=False,
            motivo=MEDIANA_ZERO,
            mediana_kg_co2e=centro,
            linhas=(),
        )

    ordenadas = sorted(elegiveis, key=lambda u: (-u.emissao_kg_co2e, u.unidade_id))

    linhas = tuple(
        LinhaComparacao(
            unidade_id=u.unidade_id,
            unidade_nome=u.unidade_nome,
            emissao_kg_co2e=u.emissao_kg_co2e,
            desvio_percentual=_desvio(u.emissao_kg_co2e, centro),
            alerta=(
                abs(u.emissao_kg_co2e - centro) * Decimal("100")
                > centro * LIMIAR_ALERTA_PERCENTUAL
            ),
        )
        for u in ordenadas
    )

    return Comparacao(
        disponivel=True,
        motivo=None,
        mediana_kg_co2e=centro,
        linhas=linhas,
    )


def _desvio(emissao: Decimal, centro: Decimal) -> Decimal:
    """Desvio percentual contra a mediana, em 2 casas.

    Duas casas porque e numero de leitura, nao de auditoria: ninguem
    confere "+63,41%" na calculadora, e tres casas num percentual so
    sugerem uma precisao que a mediana de uma rede pequena nao tem.
    """
    return ((emissao - centro) / centro * 100).quantize(Decimal("0.01"))

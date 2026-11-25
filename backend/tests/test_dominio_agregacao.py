"""Agregacao: totais por unidade, regiao e escopo, e a comparacao.

O cenario determinístico do CA-04 esta em `cenario_ca04()`, com semente e
versao registradas aqui no modulo -- quem repetir a conferencia daqui a
seis meses gera exatamente os mesmos numeros.
"""

import random
from decimal import Decimal

import pytest

from app.dominio.agregacao import (
    LIMIAR_ALERTA_PERCENTUAL,
    MEDIANA_ZERO,
    MINIMO_ELEGIVEIS,
    SEM_ELEGIVEIS,
    EmissaoNaoArredondada,
    Lancamento,
    TotalUnidade,
    agregar,
    comparar,
)

# --------------------------------------------------------------------
# Cenario do CA-04 -- semente e versao registradas
# --------------------------------------------------------------------
#
# 3 unidades, 2 regioes, 2 meses, 2 fontes. A semente fixa torna o
# conjunto reproduzivel sem precisar versionar uma tabela de numeros:
# mudar a semente muda os valores, mas nenhuma das igualdades abaixo
# depende de quais valores sao -- e esse o ponto.

SEMENTE_CA04 = 20261115
VERSAO_CENARIO_CA04 = "ca04-v1"

UNIDADES_CA04 = [
    ("asa-norte", "Loja Asa Norte", "DF"),
    ("taguatinga", "Loja Taguatinga", "DF"),
    ("goiania-cd", "Centro de Distribuicao", "GO"),
]
MESES_CA04 = ["2026-01", "2026-02"]
FONTES_CA04 = [("eletricidade", "2"), ("diesel", "1")]


def cenario_ca04() -> dict[str, list[Lancamento]]:
    """Lancamentos por competencia, gerados da semente registrada.

    Os valores sao ilustrativos e nao representam fator de emissao real,
    como o proprio CA-04 pede que se registre.
    """
    sorteio = random.Random(SEMENTE_CA04)
    por_mes: dict[str, list[Lancamento]] = {}

    for mes in MESES_CA04:
        lancamentos = []
        for unidade_id, nome, uf in UNIDADES_CA04:
            for fonte_id, escopo in FONTES_CA04:
                # Milesimos inteiros: e a escala em que o motor grava.
                milesimos = sorteio.randrange(1_000, 5_000_000)
                lancamentos.append(
                    Lancamento(
                        unidade_id=unidade_id,
                        unidade_nome=nome,
                        regiao=uf,
                        fonte_id=fonte_id,
                        escopo=escopo,
                        emissao_kg_co2e=Decimal(milesimos).scaleb(-3),
                    )
                )
        por_mes[mes] = lancamentos

    return por_mes


# --------------------------------------------------------------------
# CA-04: igualdade exata entre os recortes
# --------------------------------------------------------------------


@pytest.mark.parametrize("mes", MESES_CA04)
def test_soma_por_unidade_bate_com_o_total(mes):
    agregado = agregar(cenario_ca04()[mes], mes)
    soma = sum((u.emissao_kg_co2e for u in agregado.por_unidade), Decimal(0))
    assert soma == agregado.total_kg_co2e


@pytest.mark.parametrize("mes", MESES_CA04)
def test_soma_por_regiao_bate_com_o_total(mes):
    agregado = agregar(cenario_ca04()[mes], mes)
    soma = sum((r.emissao_kg_co2e for r in agregado.por_regiao), Decimal(0))
    assert soma == agregado.total_kg_co2e


@pytest.mark.parametrize("mes", MESES_CA04)
def test_soma_por_escopo_bate_com_o_total(mes):
    agregado = agregar(cenario_ca04()[mes], mes)
    soma = sum((e.emissao_kg_co2e for e in agregado.por_escopo), Decimal(0))
    assert soma == agregado.total_kg_co2e


@pytest.mark.parametrize("mes", MESES_CA04)
def test_recortes_batem_entre_si(mes):
    """A igualdade que o CA-04 pede, dita no sentido mais forte.

    Nao basta cada recorte bater com o total: os tres tem de ser o mesmo
    numero, com a mesma escala. `==` em Decimal compara valor, entao a
    escala vai conferida a parte.
    """
    agregado = agregar(cenario_ca04()[mes], mes)
    por_unidade = sum((u.emissao_kg_co2e for u in agregado.por_unidade), Decimal(0))
    por_regiao = sum((r.emissao_kg_co2e for r in agregado.por_regiao), Decimal(0))
    por_escopo = sum((e.emissao_kg_co2e for e in agregado.por_escopo), Decimal(0))

    assert por_unidade == por_regiao == por_escopo
    assert por_unidade.as_tuple().exponent == agregado.total_kg_co2e.as_tuple().exponent


def test_meses_sao_independentes():
    """Filtro de mes correto: janeiro nao entra no total de fevereiro."""
    cenario = cenario_ca04()
    janeiro = agregar(cenario["2026-01"], "2026-01")
    fevereiro = agregar(cenario["2026-02"], "2026-02")

    assert janeiro.competencia == "2026-01"
    assert fevereiro.competencia == "2026-02"
    assert janeiro.total_kg_co2e != fevereiro.total_kg_co2e

    juntos = agregar(cenario["2026-01"] + cenario["2026-02"], "2026-01/02")
    assert juntos.total_kg_co2e == janeiro.total_kg_co2e + fevereiro.total_kg_co2e


def test_duas_regioes_no_cenario():
    agregado = agregar(cenario_ca04()["2026-01"], "2026-01")
    assert [r.regiao for r in agregado.por_regiao] == ["DF", "GO"]
    assert [r.unidades for r in agregado.por_regiao] == [2, 1]


def test_fracoes_decimais_sobrevivem():
    """A parte fracionaria nao pode ser perdida no caminho.

    Um agregado que truncasse para inteiro passaria em todos os testes
    de igualdade acima -- e estaria errado. Este fixa a fracao.
    """
    agregado = agregar(cenario_ca04()["2026-01"], "2026-01")
    assert agregado.total_kg_co2e % 1 != 0
    assert agregado.total_kg_co2e.as_tuple().exponent == -3


def test_cenario_e_reproduzivel():
    """Mesma semente, mesmos numeros -- em qualquer maquina, sempre."""
    assert cenario_ca04()["2026-01"] == cenario_ca04()["2026-01"]


# --------------------------------------------------------------------
# Agregacao: casos conferidos a mao
# --------------------------------------------------------------------


def _lanc(unidade_id, uf, fonte, escopo, valor, nome=None, ativa=True):
    return Lancamento(
        unidade_id=unidade_id,
        unidade_nome=nome or unidade_id,
        regiao=uf,
        fonte_id=fonte,
        escopo=escopo,
        emissao_kg_co2e=Decimal(valor),
        unidade_ativa=ativa,
    )


def test_total_conferido_a_mao():
    """57,750 + 42,600 + 11,300 = 111,650."""
    agregado = agregar(
        [
            _lanc("a", "DF", "eletricidade", "2", "57.750"),
            _lanc("b", "DF", "eletricidade", "2", "42.600"),
            _lanc("c", "GO", "diesel", "1", "11.300"),
        ],
        "2026-01",
    )
    assert agregado.total_kg_co2e == Decimal("111.650")
    assert agregado.por_regiao[0].emissao_kg_co2e == Decimal("100.350")
    assert agregado.por_regiao[1].emissao_kg_co2e == Decimal("11.300")


def test_varias_fontes_na_mesma_unidade_somam():
    agregado = agregar(
        [
            _lanc("a", "DF", "eletricidade", "2", "57.750"),
            _lanc("a", "DF", "diesel", "1", "11.300"),
        ],
        "2026-01",
    )
    assert len(agregado.por_unidade) == 1
    assert agregado.por_unidade[0].emissao_kg_co2e == Decimal("69.050")
    assert agregado.por_unidade[0].fontes_lancadas == 2


def test_escopos_separados():
    agregado = agregar(
        [
            _lanc("a", "DF", "eletricidade", "2", "57.750"),
            _lanc("a", "DF", "diesel", "1", "11.300"),
        ],
        "2026-01",
    )
    assert [(e.escopo, e.emissao_kg_co2e) for e in agregado.por_escopo] == [
        ("1", Decimal("11.300")),
        ("2", Decimal("57.750")),
    ]


def test_unidades_vem_da_maior_para_a_menor():
    agregado = agregar(
        [
            _lanc("pequena", "DF", "eletricidade", "2", "10.000"),
            _lanc("grande", "DF", "eletricidade", "2", "90.000"),
            _lanc("media", "DF", "eletricidade", "2", "50.000"),
        ],
        "2026-01",
    )
    assert [u.unidade_id for u in agregado.por_unidade] == [
        "grande",
        "media",
        "pequena",
    ]


def test_empate_desempata_pelo_id():
    """Ordem estavel: duas telas abertas lado a lado mostram o mesmo."""
    agregado = agregar(
        [
            _lanc("zebra", "DF", "eletricidade", "2", "10.000"),
            _lanc("alfa", "DF", "eletricidade", "2", "10.000"),
        ],
        "2026-01",
    )
    assert [u.unidade_id for u in agregado.por_unidade] == ["alfa", "zebra"]


def test_unidade_desativada_continua_no_total():
    """CA-05: desativar nao apaga historico."""
    agregado = agregar(
        [_lanc("fechada", "DF", "eletricidade", "2", "57.750", ativa=False)],
        "2026-01",
    )
    assert agregado.total_kg_co2e == Decimal("57.750")
    assert agregado.por_unidade[0].unidade_ativa is False


def test_sem_lancamentos_da_zero_e_nao_erro():
    agregado = agregar([], "2026-01")
    assert agregado.total_kg_co2e == Decimal(0)
    assert agregado.por_unidade == ()


def test_emissao_com_casas_demais_e_recusada():
    """Guarda da igualdade exata: uma parcela fora de escala estraga tudo."""
    with pytest.raises(EmissaoNaoArredondada) as erro:
        agregar([_lanc("a", "DF", "eletricidade", "2", "57.7500001")], "2026-01")
    assert "3 casas" in str(erro.value)


def test_zero_explicito_entra_na_agregacao():
    """Zero e coleta feita, nao ausencia (CA-05)."""
    agregado = agregar(
        [
            _lanc("a", "DF", "diesel", "1", "0.000"),
            _lanc("b", "DF", "eletricidade", "2", "57.750"),
        ],
        "2026-01",
    )
    assert len(agregado.por_unidade) == 2
    assert agregado.total_kg_co2e == Decimal("57.750")


# --------------------------------------------------------------------
# CA-06: comparacao contra a mediana
# --------------------------------------------------------------------


def _total(unidade_id, valor):
    return TotalUnidade(
        unidade_id=unidade_id,
        unidade_nome=unidade_id,
        regiao="DF",
        emissao_kg_co2e=Decimal(valor),
        fontes_lancadas=1,
        unidade_ativa=True,
    )


def test_comparacao_indisponivel_com_menos_de_tres():
    comp = comparar([_total("a", "100.000"), _total("b", "200.000")])
    assert comp.disponivel is False
    assert comp.motivo == SEM_ELEGIVEIS
    assert comp.linhas == ()


def test_tres_elegiveis_e_o_minimo_que_funciona():
    comp = comparar([_total(x, "100.000") for x in ("a", "b", "c")])
    assert comp.disponivel is True
    assert MINIMO_ELEGIVEIS == 3


def test_mediana_zero_deixa_a_comparacao_indisponivel():
    """Rede inteira em zero: dividir por zero nao e a resposta."""
    comp = comparar([_total(x, "0.000") for x in ("a", "b", "c")])
    assert comp.disponivel is False
    assert comp.motivo == MEDIANA_ZERO


def test_desvio_conferido_a_mao():
    """Mediana de 100, 200, 300 = 200. Desvios: -50%, 0%, +50%."""
    comp = comparar(
        [_total("a", "100.000"), _total("b", "200.000"), _total("c", "300.000")]
    )
    assert comp.mediana_kg_co2e == Decimal("200.000")
    por_id = {linha.unidade_id: linha for linha in comp.linhas}
    assert por_id["a"].desvio_percentual == Decimal("-50.00")
    assert por_id["b"].desvio_percentual == Decimal("0.00")
    assert por_id["c"].desvio_percentual == Decimal("50.00")


def test_cinquenta_por_cento_exato_nao_alerta():
    """A fronteira do CA-06, nos dois sentidos.

    O criterio diz "acima de 50%". Exatamente 50% nao alerta -- e o tipo
    de limite que vira defeito se alguem escrever >= por descuido.
    """
    comp = comparar(
        [_total("a", "100.000"), _total("b", "200.000"), _total("c", "300.000")]
    )
    assert all(linha.alerta is False for linha in comp.linhas)
    assert LIMIAR_ALERTA_PERCENTUAL == Decimal("50")


def test_acima_de_cinquenta_alerta():
    """301 contra mediana 200 = +50,50%: passa da fronteira."""
    comp = comparar(
        [_total("a", "100.000"), _total("b", "200.000"), _total("c", "301.000")]
    )
    por_id = {linha.unidade_id: linha for linha in comp.linhas}
    assert por_id["c"].desvio_percentual == Decimal("50.50")
    assert por_id["c"].alerta is True


def test_abaixo_de_menos_cinquenta_tambem_alerta():
    """O alerta e sobre desvio absoluto: consumo baixo demais tambem.

    Uma loja muito abaixo da mediana costuma significar coleta faltando,
    nao eficiencia -- e e isso que vale investigar.
    """
    comp = comparar(
        [_total("a", "99.000"), _total("b", "200.000"), _total("c", "300.000")]
    )
    por_id = {linha.unidade_id: linha for linha in comp.linhas}
    assert por_id["a"].desvio_percentual == Decimal("-50.50")
    assert por_id["a"].alerta is True


def test_ranking_decrescente_com_empate_pelo_id():
    comp = comparar(
        [
            _total("zebra", "200.000"),
            _total("alfa", "200.000"),
            _total("meio", "150.000"),
        ]
    )
    assert [linha.unidade_id for linha in comp.linhas] == ["alfa", "zebra", "meio"]


def test_mediana_de_numero_par_de_unidades():
    """Quatro unidades: mediana e a media das duas do meio."""
    comp = comparar(
        [
            _total("a", "100.000"),
            _total("b", "200.000"),
            _total("c", "300.000"),
            _total("d", "400.000"),
        ]
    )
    assert comp.mediana_kg_co2e == Decimal("250.000")


@pytest.mark.parametrize(
    "menor,maior,alerta_menor,alerta_maior",
    [
        ("50.001", "149.999", False, False),
        ("50.000", "150.000", False, False),
        ("49.999", "150.001", True, True),
        ("50.000", "150.001", False, True),
        ("49.999", "150.000", True, False),
    ],
)
def test_alerta_usa_desvio_sem_arredondamento(
    menor, maior, alerta_menor, alerta_maior
):
    comp = comparar(
        [
            _total("a", menor),
            _total("b", "100.000"),
            _total("c", maior),
        ]
    )
    assert comp.disponivel is True
    assert comp.mediana_kg_co2e == Decimal("100.000")

    por_id = {linha.unidade_id: linha for linha in comp.linhas}
    assert por_id["a"].alerta is alerta_menor
    assert por_id["b"].alerta is False
    assert por_id["c"].alerta is alerta_maior

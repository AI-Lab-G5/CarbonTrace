"""Calculo de emissoes e consolidacao da rede.

Funcoes puras, sem Firestore. Isso as torna testaveis sem subir nada e
e o que permite provar, no Demo Day, que recalcular um periodo antigo
com o fator da epoca devolve exatamente o mesmo numero.
"""

from statistics import median

from app.models import Fator


def calcular_emissao(quantidade: float, fator: Fator) -> float:
    """Converte uma quantidade consumida em kg de CO2 equivalente.

    Deliberadamente trivial: a confiabilidade do numero nao vem da
    formula, vem de qual versao do fator foi usada. Por isso o fator
    entra como argumento, e nunca e buscado aqui dentro.
    """
    if quantidade < 0:
        raise ValueError("quantidade nao pode ser negativa")
    return round(quantidade * fator.kg_co2e_por_unidade, 6)


def consolidar(emissoes_por_unidade: dict[str, float]) -> tuple[float, float]:
    """Total e mediana da rede.

    A mediana -- e nao a media -- porque uma unica unidade gigante
    distorce a media e faz toda comparacao entre lojas perder sentido.
    """
    if not emissoes_por_unidade:
        return 0.0, 0.0
    valores = list(emissoes_por_unidade.values())
    return round(sum(valores), 6), round(median(valores), 6)


def desvio_da_mediana(valor: float, mediana: float) -> float | None:
    """Quanto uma unidade se afasta da mediana da rede, em porcentagem.

    Devolve None quando a mediana e zero, porque nao existe variacao
    percentual sobre zero.
    """
    if mediana == 0:
        return None
    return round((valor - mediana) / mediana * 100, 2)

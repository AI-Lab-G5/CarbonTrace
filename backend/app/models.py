"""Contratos de entrada e saida da API.

Quantidades e fatores trafegam como texto. Pydantic ja serializa Decimal
como string em JSON; na entrada, o validador recusa numero decimal para
que o front nao mande 0.30000000000000004 sem perceber.
"""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field, field_validator

from app.dominio.competencia import validar as validar_competencia
from app.dominio.erros import CompetenciaInvalida
from app.dominio.numeros import ValorNaoDecimal, para_decimal

Escopo = Literal["1", "2"]
StatusFator = Literal["preliminar", "vigente", "substituido"]


def _decimal_de_texto(valor: object) -> object:
    """Converte texto em Decimal, recusando float.

    Devolve ValueError para o Pydantic transformar em 422 com o caminho
    do campo -- mensagem util para o front saber onde errou.
    """
    try:
        return para_decimal(valor, campo="quantidade")
    except ValorNaoDecimal as erro:
        raise ValueError(str(erro)) from erro


Quantidade = Annotated[Decimal, BeforeValidator(_decimal_de_texto)]


class Unidade(BaseModel):
    """Uma loja, filial ou franquia da rede."""

    id: str | None = None
    nome: str = Field(min_length=1, max_length=120)
    cidade: str = Field(min_length=1, max_length=120)
    uf: str = Field(min_length=2, max_length=2)

    @field_validator("uf")
    @classmethod
    def uf_maiuscula(cls, v: str) -> str:
        return v.upper()

    @field_validator("nome", "cidade")
    @classmethod
    def sem_espaco_sobrando(cls, v: str) -> str:
        limpo = v.strip()
        if not limpo:
            raise ValueError("Campo nao pode ser so espaco.")
        return limpo


class ConsumoEntrada(BaseModel):
    """Lancamento mensal de uma fonte numa unidade."""

    unidade_id: str = Field(min_length=1)
    competencia: str = Field(description="Mes de referencia, formato AAAA-MM")
    fonte_id: str = Field(min_length=1)
    quantidade: Quantidade = Field(description="Texto, ex.: \"1500.5\"")
    unidade_medida: str = Field(min_length=1, max_length=10)

    @field_validator("competencia")
    @classmethod
    def competencia_valida(cls, v: str) -> str:
        try:
            return validar_competencia(v)
        except CompetenciaInvalida as erro:
            raise ValueError(erro.mensagem()) from erro


class Consumo(BaseModel):
    """Lancamento ja calculado e persistido.

    Guarda a versao e o valor do fator aplicado. E o que permite
    recalcular o periodo depois, com o fator da epoca, e obter o
    mesmo numero.
    """

    id: str
    unidade_id: str
    competencia: str
    fonte_id: str
    quantidade_informada: Decimal
    unidade_informada: str
    quantidade_convertida: Decimal
    unidade_base: str
    fator_versao: str
    fator_valor: Decimal
    emissao_kg_co2e: Decimal
    escopo: Escopo


class Fator(BaseModel):
    """Fator de conversao de uma fonte de emissao."""

    fonte_id: str
    nome: str
    escopo: Escopo
    unidade_base: str
    unidades_aceitas: list[str]
    kg_co2e_por_unidade: Decimal
    teto_mensal: Decimal = Field(
        description=(
            "Quantidade maxima aceita num lancamento mensal, na unidade "
            "base. Conferido DEPOIS da conversao de unidade: 1001 MWh sao "
            "comparados como 1.001.000 kWh. Valores vigentes: eletricidade "
            "1000000 kWh, diesel 200000 L, gasolina 100000 L, GLP 50000 kg. "
            "E um filtro contra erro de digitacao, nao um limite de "
            "negocio; o valor vem do catalogo e muda publicando versao nova."
        )
    )
    fonte_referencia: str
    status: StatusFator


class VersaoFatores(BaseModel):
    """Conjunto imutavel de fatores, identificado por versao."""

    versao: str
    vigencia_inicio: str
    vigencia_fim: str | None = None
    publicado_em: str
    status: StatusFator
    fatores: list[Fator]


class LinhaConsolidado(BaseModel):
    unidade_id: str
    unidade_nome: str
    emissao_kg_co2e: Decimal


class Consolidado(BaseModel):
    """Agregado da rede numa competencia."""

    competencia: str
    total_kg_co2e: Decimal
    mediana_kg_co2e: Decimal
    por_unidade: list[LinhaConsolidado]


class TotalRegiaoSaida(BaseModel):
    regiao: str = Field(description="UF da unidade, enquanto a #34 nao redefine")
    emissao_kg_co2e: Decimal
    unidades: int


class TotalEscopoSaida(BaseModel):
    escopo: Escopo
    emissao_kg_co2e: Decimal


class LinhaUnidade(BaseModel):
    """Total de uma unidade dentro de um snapshot."""

    unidade_id: str
    unidade_nome: str
    regiao: str
    emissao_kg_co2e: Decimal
    fontes_lancadas: int
    unidade_ativa: bool
    posicao: int = Field(description="Posicao no ranking, 1 = maior emissao")


class SnapshotResumo(BaseModel):
    """Cabecalho de um snapshot, sem as linhas por unidade."""

    id: str
    competencia: str
    versao: int
    gerado_em: str
    gerado_por_uid: str
    impressao_digital: str = Field(
        description=(
            "Resumo do conteudo. Gerar de novo a mesma competencia sem "
            "mudanca nos lancamentos devolve este mesmo snapshot."
        )
    )
    total_kg_co2e: Decimal
    unidades_no_total: int


class Snapshot(SnapshotResumo):
    """Snapshot com os totais por regiao e por escopo.

    As linhas por unidade nao vem aqui: ficam em
    GET /v1/snapshots/{id}/unidades, paginadas, para que uma rede grande
    nao devolva tudo numa resposta so.
    """

    por_regiao: list[TotalRegiaoSaida]
    por_escopo: list[TotalEscopoSaida]


class GeracaoSnapshot(BaseModel):
    """Pedido de geracao de snapshot."""

    competencia: str = Field(description="Mes de referencia, formato AAAA-MM")

    @field_validator("competencia")
    @classmethod
    def competencia_valida(cls, v: str) -> str:
        try:
            return validar_competencia(v)
        except CompetenciaInvalida as erro:
            raise ValueError(erro.mensagem()) from erro


class SnapshotGerado(BaseModel):
    """Resposta da geracao.

    `criado=False` com 200 significa reenvio sem mudanca nos lancamentos:
    nenhuma versao nova nasceu e o snapshot devolvido e o que ja existia.
    """

    criado: bool
    snapshot: Snapshot


class LinhaComparacaoSaida(BaseModel):
    unidade_id: str
    unidade_nome: str
    emissao_kg_co2e: Decimal
    desvio_percentual: Decimal = Field(description="Contra a mediana, em %")
    alerta: bool = Field(
        description="Verdadeiro so quando o desvio absoluto passa de 50%"
    )


class ComparacaoSaida(BaseModel):
    """Ranking e desvio contra a mediana (CA-06).

    `disponivel=False` nao e erro: a rede nao tem base de comparacao.
    O motivo acompanha para a tela poder explicar.
    """

    competencia: str
    snapshot_id: str
    disponivel: bool
    motivo: str | None = None
    mediana_kg_co2e: Decimal
    elegiveis: int
    linhas: list[LinhaComparacaoSaida]


class Pagina[T](BaseModel):
    """Uma fatia de uma listagem.

    Existe para que nenhuma rota de lista possa devolver um numero
    ilimitado de documentos. Uma rede grande com dois anos de historico
    tem dezenas de milhares de lancamentos; sem limite, a primeira
    chamada derruba o navegador e paga a leitura de todos eles no
    Firestore.

    O cursor e o id do ultimo item devolvido. Paginar por cursor, e nao
    por numero de pagina, e o que o Firestore faz bem -- e nao pula nem
    repete item quando alguem lanca um consumo entre uma pagina e outra.
    """

    itens: list[T]
    total_na_pagina: int
    limite: int
    proximo_cursor: str | None = Field(
        default=None,
        description="Passe em 'cursor' para a proxima pagina. Nulo no fim.",
    )


class Erro(BaseModel):
    """Resposta de erro da API.

    Formato unico para o front tratar todos os casos do mesmo jeito.
    """

    detalhe: str
    codigo: str

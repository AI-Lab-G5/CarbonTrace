"""Modelos de entrada e saida da API."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

COMPETENCIA_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

Escopo = Literal["1", "2", "3"]


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


class RegistroEntrada(BaseModel):
    """Lancamento mensal de uma fonte de emissao em uma unidade."""

    unidade_id: str = Field(min_length=1)
    competencia: str = Field(description="Mes de referencia, no formato AAAA-MM")
    fonte_id: str = Field(min_length=1, description="Ex.: energia_eletrica_sin")
    quantidade: float = Field(gt=0)

    @field_validator("competencia")
    @classmethod
    def competencia_valida(cls, v: str) -> str:
        if not COMPETENCIA_RE.match(v):
            raise ValueError("competencia deve estar no formato AAAA-MM")
        return v


class Registro(BaseModel):
    """Lancamento ja calculado e persistido."""

    id: str
    unidade_id: str
    competencia: str
    fonte_id: str
    quantidade: float
    unidade_medida: str
    fator_versao: str
    fator_valor: float
    emissao_kg_co2e: float
    escopo: Escopo


class Fator(BaseModel):
    """Fator de conversao de uma fonte de emissao."""

    fonte_id: str
    nome: str
    escopo: Escopo
    unidade_medida: str
    kg_co2e_por_unidade: float
    fonte_referencia: str


class VersaoFatores(BaseModel):
    """Conjunto imutavel de fatores, identificado por versao."""

    versao: str
    vigencia_inicio: str
    publicado_em: str
    fatores: list[Fator]


class LinhaConsolidado(BaseModel):
    unidade_id: str
    unidade_nome: str
    emissao_kg_co2e: float


class Consolidado(BaseModel):
    """Agregado da rede em uma competencia."""

    competencia: str
    total_kg_co2e: float
    mediana_kg_co2e: float
    por_unidade: list[LinhaConsolidado]

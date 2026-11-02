export interface Unidade { id: string; nome: string; cidade: string; uf: string }
export interface Pagina<T> { itens: T[]; total_na_pagina: number; limite: number; proximo_cursor: string | null }
export interface Fator { fonte_id: string; nome: string; unidades_aceitas: string[]; unidade_base: string; kg_co2e_por_unidade: string; teto_mensal: string; fonte_referencia: string; status: string }
export interface Versao { versao: string; fatores: Fator[]; vigencia_inicio: string; status: string }
export interface Consumo { id: string; unidade_id: string; competencia: string; fonte_id: string; quantidade_informada: string; unidade_informada: string; quantidade_convertida: string; unidade_base: string; fator_versao: string; fator_valor: string; emissao_kg_co2e: string; escopo: string }

# Rastreabilidade de requisitos e testes

**Projeto:** CarbonTrace
**Revisão avaliada:** `5a35330` (`main`, merge do PR #30)
**Data:** 06/11/2026
**Issue responsável:** [#24](https://github.com/AI-Lab-G5/CarbonTrace/issues/24) — CA-05

Esta matriz liga **critério individual → teste executável → resultado → versão/PR/CI**.
Ela complementa o [relatório de testes v1](relatorio-testes-v1.md), que traz ambiente,
comandos e totais.

Os critérios vêm do [MoSCoW do repositório de documentação](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/backlog/MoSCoW.md)
e conservam a numeração original (CT-M01 a CT-M05, CT-M09). A matriz de capacidades
daquele repositório **não substitui** esta, que é o artefato de QA exigido pelo DoD.

## Como ler os resultados

| Marca | Significado |
| --- | --- |
| **Coberto** | Existe teste executável e ele passa na revisão indicada |
| **Parcial** | Parte do critério tem teste; o restante está descrito na coluna Lacuna |
| **Lacuna** | O comportamento **não está implementado**; nenhum teste pode cobri-lo |
| **Fora do CP2** | Adiado pelo ADR-008, não bloqueia J1–J3 |

`Lacuna` não é falha de teste: é comportamento ausente no código. Teste não pode
aprovar o que não existe.

---

## CT-M01 — Unidades e fontes (J1)

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 1.1a | Rejeitar nome/cidade vazios ou só com espaços | `test_api_validacao.py::test_campo_obrigatorio_vazio_e_recusado`, `::test_nome_so_com_espaco_e_recusado` | **Coberto** | — |
| 1.1b | Rejeitar nome acima de 120 caracteres | `test_api_validacao.py::test_nome_longo_demais_e_recusado` | **Coberto** | — |
| 1.1c | UF com 2 letras, normalizada para maiúscula | `test_api_validacao.py::test_uf_com_tamanho_errado_e_recusada`, `::test_uf_e_normalizada_para_maiuscula` | **Coberto** | — |
| 1.1d | Código repetido na mesma empresa → HTTP 409 | — | **Lacuna** | `Unidade` não tem campo `codigo`; `POST /v1/unidades` cria documento novo sem verificar duplicata (`app/routers/unidades.py:42`) |
| 1.1e | Editar loja existente | — | **Lacuna** | Não existe `PUT`/`PATCH` em `/v1/unidades` |
| 1.2a | Catálogo traz as 4 fontes aprovadas | `test_api_consumos.py::test_catalogo_traz_as_quatro_fontes_aprovadas` | **Coberto** | — |
| 1.2b | Catálogo informa as unidades aceitas por fonte | `test_api_consumos.py::test_catalogo_informa_as_unidades_aceitas` | **Coberto** | — |
| 1.2c | Rejeitar fonte fora do catálogo | `test_api_consumos.py::test_fonte_fora_do_catalogo` | **Coberto** | — |
| 1.2d | Vincular/desvincular fonte **por loja** | — | **Lacuna** | Não há rota de vínculo fonte↔unidade; `/v1/fontes` é catálogo global |
| 1.3a | Paginação padrão 20, máximo 100 | `test_api_paginacao.py::test_limite_padrao_nao_e_ilimitado`, `::test_limite_acima_do_maximo_e_recusado` | **Coberto** | — |
| 1.3b | Percorrer tudo sem repetir nem pular | `test_api_paginacao.py::test_percorrer_tudo_nao_repete_nem_pula` | **Coberto** | — |
| 1.3c | Estados de interface: carregando, vazio, erro, sucesso | — | **Fora do CP2** | Depende do frontend integrado (#9/#19), que está na branch `dev` e não foi testado nesta revisão |
| 1.4 | Desativação bloqueia coleta nova e preserva histórico | — | **Lacuna** | Desativação não implementada (não há `DELETE`/flag `ativa`) |

**Resumo CT-M01: 9 cobertos, 3 lacunas, 1 fora do CP2.**

## CT-M02 — Login e isolamento

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 2.1a | Sem token → 401, em todas as rotas protegidas | `test_autorizacao.py::test_sem_token_e_barrado` (11 rotas) | **Coberto** | — |
| 2.1b | Token expirado → 401 com mensagem de expiração | `test_autorizacao.py::test_token_expirado_e_barrado` (11 rotas) | **Coberto** | — |
| 2.1c | Papel diferente de `funcionario` → 403 | `test_autorizacao.py::test_papel_errado_e_barrado` (11 rotas) | **Coberto** | — |
| 2.1d | Token sem vínculo com empresa → 403 | `test_autorizacao.py::test_usuario_sem_empresa_e_barrado` (11 rotas) | **Coberto** | — |
| 2.1e | Cabeçalho malformado (Bearer vazio, Basic) → 401 | `test_autorizacao.py::test_bearer_vazio_e_barrado`, `::test_esquema_errado_e_barrado` | **Coberto** | — |
| 2.1f | `/healthz` e `/readyz` continuam públicas | `test_autorizacao.py::test_rotas_publicas_respondem_sem_token` | **Coberto** | — |
| 2.2a | Empresa B não lê unidade da empresa A | `test_isolamento_tenant.py::test_unidade_de_outra_empresa_nao_e_acessivel` | **Coberto** | — |
| 2.2b | Empresa B não lê consumo da empresa A | `test_isolamento_tenant.py::test_consumo_de_outra_empresa_nao_e_acessivel` | **Coberto** | — |
| 2.2c | Empresa B não recalcula consumo alheio | `test_isolamento_tenant.py::test_recalculo_de_consumo_alheio_e_barrado` | **Coberto** | — |
| 2.2d | Listagens não misturam tenants | `test_isolamento_tenant.py::test_listagem_de_unidades_nao_mistura`, `::test_listagem_de_consumos_nao_mistura` | **Coberto** | — |
| 2.2e | Não lança consumo em unidade alheia | `test_isolamento_tenant.py::test_nao_lanca_consumo_em_unidade_alheia` | **Coberto** | — |
| 2.2f | Consolidado ignora dados de outra empresa | `test_isolamento_tenant.py::test_consolidado_de_outra_empresa_ignora_dados_alheios` | **Coberto** | — |
| 2.2g | Empresa A acessa suas próprias unidades | fixtures `como_funcionario` usadas em toda a suíte | **Coberto** | — |
| 2.3 | Bloqueio direto ao Firestore (Rules) | `qa/test_deny_all.py` — 9 casos | **Coberto** | — |

**Resumo CT-M02: 14 cobertos, 0 lacunas.** É o critério mais bem coberto do conjunto.

**Nota de método:** os testes de 2.1 substituem o verificador de ID token do Firebase
por uma fixture. O que eles provam é a *nossa* autorização — que o `tenant_id` vem da
claim e não do cliente. A assinatura do token é código do Firebase e não está no escopo.

## CT-M03 — Coleta mensal validada (J2)

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 3.1a | Competência no formato `AAAA-MM` | `test_dominio_competencia.py::test_formato_valido`, `::test_formatos_invalidos` (14 casos) | **Coberto** | — |
| 3.1b | Mês 00 e 13 recusados; 01 e 12 aceitos | `test_dominio_competencia.py::test_mes_zero_e_recusado`, `::test_mes_treze_e_recusado`, `::test_janeiro_e_dezembro_passam` | **Coberto** | — |
| 3.1c | Competência futura recusada | `test_dominio_competencia.py::test_mes_seguinte_e_recusado`, `::test_ano_seguinte_e_recusado` | **Coberto** | — |
| 3.1d | Piso do catálogo: exatamente no piso passa, abaixo recusa | `test_dominio_competencia.py::test_exatamente_no_piso_passa`, `::test_logo_abaixo_do_piso_e_recusado` | **Coberto** | — |
| 3.1e | Quantidade zero aceita | `test_dominio_calculo.py::test_zero_e_aceito`, `test_api_consumos.py::test_zero_e_gravado_como_lancamento` | **Coberto** | — |
| 3.1f | Quantidade negativa recusada | `test_dominio_calculo.py::test_negativo_e_recusado`, `::test_negativo_grande_e_recusado` | **Coberto** | — |
| 3.1g | Teto: abaixo passa, no teto passa, acima recusa | `test_dominio_calculo.py::test_logo_abaixo_do_teto_passa`, `::test_exatamente_no_teto_passa`, `::test_logo_acima_do_teto_e_recusado` | **Coberto** | — |
| 3.1h | Teto conferido **depois** da conversão de unidade | `test_dominio_calculo.py::test_teto_e_conferido_depois_da_conversao` | **Coberto** | — |
| 3.1i | Unidade desconhecida e unidade de outra fonte recusadas | `test_dominio_calculo.py::test_unidade_desconhecida_e_recusada`, `::test_unidade_de_outra_fonte_e_recusada` | **Coberto** | — |
| 3.1j | Ausente, não finito, `float`, `bool`, lista recusados | `test_dominio_numeros.py` (18 casos: `test_none_e_recusado`, `test_nan_e_recusado`, `test_infinito_e_recusado`, `test_float_e_recusado`, `test_booleano_e_recusado`, `test_lista_e_recusada`) | **Coberto** | — |
| 3.1k | Exatidão decimal preservada | `test_dominio_numeros.py::test_exatidao_preservada_onde_float_falharia` | **Coberto** | — |
| 3.2a | Guarda a quantidade **original** e a unidade informada | `test_api_consumos.py::test_numeros_trafegam_como_texto`; campos `quantidade_informada`/`unidade_informada` em `Consumo` | **Coberto** | — |
| 3.2b | Guarda **autoria** (quem lançou) | — | **Lacuna** | `Consumo` não tem campo de autor; `persistencia.py` não grava `uid` |
| 3.2c | Guarda **data** do lançamento | — | **Lacuna** | `Consumo` não tem campo de data/hora |
| 3.3a | Reenvio do mesmo lançamento não duplica | `test_api_consumos.py::test_lancamento_repetido_sobrescreve` | **Coberto** | — |
| 3.3b | Correção substitui o valor anterior | `test_api_consumos.py::test_correcao_substitui_o_valor_anterior` | **Coberto** | — |

**Resumo CT-M03: 16 cobertos, 2 lacunas.**

**Atenção ao 3.3a — não é idempotência de 24 h.** O `PUT /v1/consumos` é idempotente
por chave natural `(unidade, competência, fonte)`: reenviar sobrescreve. A janela de
24 h com chave de idempotência explícita continua adiada pelo ADR-008 e **não** bloqueia
o CP2. Não declare como entregue.

## CT-M04 — Fatores versionados (J3)

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 4.1 | Versões de fator com vigência própria | `test_api_consumos.py::test_competencia_de_2025_usa_a_versao_de_2025`, `::test_competencia_de_2026_usa_a_versao_nova` | **Coberto** | — |
| 4.2 | Selecionar a versão compatível com o mês | idem 4.1 | **Coberto** | — |
| 4.3 | Consultar versão e conjunto publicados | `test_api_consumos.py::test_catalogo_traz_as_quatro_fontes_aprovadas`; rotas `/v1/fontes/versoes` e `/v1/fontes/versoes/{versao}` | **Coberto** | — |
| 4.4 | Identificar fatores sintéticos ou preliminares | `test_api_consumos.py::test_catalogo_marca_o_status_preliminar` | **Coberto** | — |

**Resumo CT-M04: 4 cobertos, 0 lacunas.**

## CT-M05 — Cálculo reproduzível (J3)

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 5.1 | MWh convertido para kWh antes do cálculo | `test_dominio_calculo.py::test_mwh_converte_para_kwh`, `test_api_consumos.py::test_mwh_e_convertido_antes_do_calculo` | **Coberto** | — |
| 5.2 | Cálculo com Decimal, sem `float` | `test_dominio_numeros.py` (18 casos, incl. `::test_exatidao_preservada_onde_float_falharia`), `test_dominio_calculo.py::test_calculo_de_eletricidade_em_kwh` | **Coberto** | — |
| 5.3 | Arredondamento `ROUND_HALF_EVEN` com 3 casas | `test_dominio_calculo.py::test_empate_arredonda_para_o_par_para_baixo`, `::test_empate_arredonda_para_o_par_para_cima`, `::test_arredondamento_vem_depois_da_multiplicacao` | **Coberto** | — |
| 5.4a | Guarda consumo original, conversão, resultado, valor e versão do fator | `test_dominio_calculo.py::test_resultado_guarda_a_versao_e_o_valor_do_fator` | **Coberto** | — |
| 5.4b | Guarda autoria e data | — | **Lacuna** | mesma de 3.2b/3.2c |
| 5.5 | Fator novo **não** altera resultado já calculado | `test_dominio_calculo.py::test_versao_nova_nao_altera_resultado_anterior`, `::test_recalculo_com_o_fator_original_mantem_o_resultado`, `::test_mesma_entrada_e_mesmo_fator_dao_o_mesmo_resultado` | **Coberto** | — |
| 5.6 | Recálculo recusa fator de outra versão | `test_dominio_calculo.py::test_recalculo_recusa_fator_de_outra_versao` | **Coberto** | — |
| 5.7 | Cálculo conferido à mão ponta a ponta | `test_api_consumos.py::test_fluxo_completo_de_lancamento` (1500 kWh × 0,0426 = 63,900 kgCO2e) | **Coberto** | — |
| 5.8 | Recálculo devolve o mesmo número | `test_api_consumos.py::test_recalculo_devolve_o_mesmo_numero` | **Coberto** | — |

**Resumo CT-M05: 8 cobertos, 1 lacuna.**

## CT-M09 — Origem do resultado

| # | Critério individual | Teste executável | Resultado | Lacuna |
| --- | --- | --- | --- | --- |
| 9.1 | Consultar os dados que explicam o resultado | `test_dominio_calculo.py::test_resultado_guarda_a_versao_e_o_valor_do_fator` | **Coberto** | campos presentes: `quantidade_informada`, `unidade_informada`, `quantidade_convertida`, `unidade_base`, `fator_versao`, `fator_valor`, `emissao_kg_co2e`, `escopo` |
| 9.2 | Autoria e data na origem do resultado | — | **Lacuna** | igual a 3.2b/3.2c |

**Resumo CT-M09: 1 coberto, 1 lacuna.**

---

## Consolidado

| Critério | Coberto | Lacuna | Fora do CP2 |
| --- | ---: | ---: | ---: |
| CT-M01 Unidades e fontes | 9 | 3 | 1 |
| CT-M02 Login e isolamento | 14 | 0 | 0 |
| CT-M03 Coleta validada | 16 | 2 | 0 |
| CT-M04 Fatores versionados | 4 | 0 | 0 |
| CT-M05 Cálculo reproduzível | 8 | 1 | 0 |
| CT-M09 Origem do resultado | 1 | 1 | 0 |
| **Total** | **52** | **7** | **1** |

## Lacunas e a issue responsável

| ID | Lacuna | Critério | Issue responsável |
| --- | --- | --- | --- |
| L-01 | `Unidade` sem campo `codigo`; sem verificação de duplicata 409 | CT-M01.1d | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) (Backend) |
| L-02 | Sem `PUT`/`PATCH` para editar loja | CT-M01.1e | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) |
| L-03 | Sem rota de vínculo fonte ↔ loja | CT-M01.2d | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) |
| L-04 | Sem desativação de loja/fonte com preservação de histórico | CT-M01.4 | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) |
| L-05 | `Consumo` sem autoria | CT-M03.2b, CT-M05.4b, CT-M09.2 | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) |
| L-06 | `Consumo` sem data/hora de lançamento | idem | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) |

Estas lacunas correspondem ao que o registro do PO já apontou como **"diferenças do
núcleo, como cadastro, autoria, competência, tetos e arredondamento, precisam de
decisão"** (01/11). Não são novidade desta matriz: são a mesma pendência, agora com
número.

## Evidência de CI

| Job | Run | Resultado |
| --- | --- | --- |
| `lint` (OpenAPI) | `41654224125` | verde |
| `test-backend` (182 testes) | `41654224125` | verde |
| `lint-frontend` | `41654224125` | verde |
| `build-frontend` | `41654224125` | verde |
| `deny-all` (9 testes) | `41654224125` | verde |

O bloqueio de merge com falha **não está comprovado**: o ruleset consultado pelo PO
estava desativado. Registrado como pendência do CA-09, não como aprovado.

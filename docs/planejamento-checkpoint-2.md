# Planejamento do Checkpoint 2 - revisão de 25/10/2026

Fonte de produto: [ADR-008](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/adr/ADR-008-recorte-crud.md), [backlog](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/backlog/MoSCoW.md) e [revisão datada da S3](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/backlog/revisao-2026-10-25-s3.md). A ficha Pegada Rede do Guia para os POs limita o CP2 a J1-J3 locais; não dispensa pendências anteriores nem critérios técnicos do tutor.

## Recorte e distribuição

Um funcionário, login individual e unidades da própria empresa; quatro fontes aprovadas (eletricidade, diesel, gasolina e GLP). J1 cadastra unidades/fontes; J2 registra e consulta consumos mensais validados; J3 calcula e consulta resultados com fatores versionados. Entrada/fator/resultado originais devem permanecer reproduzíveis após B. Decimal/strings e arredondamento ROUND_HALF_EVEN; sem gestão de usuários/fatores na interface.

| Área / responsável | Sprint 2, até 25/10 | Sprint 3, até 01/11 |
| --- | --- | --- |
| PO / @Thomas4ugust0 | [#5](https://github.com/AI-Lab-G5/CarbonTrace/issues/5) | [#15](https://github.com/AI-Lab-G5/CarbonTrace/issues/15) |
| Tech Lead / @pontesluis | [#7](https://github.com/AI-Lab-G5/CarbonTrace/issues/7) | [#18](https://github.com/AI-Lab-G5/CarbonTrace/issues/18) |
| Frontend / @heitormontt | [#9](https://github.com/AI-Lab-G5/CarbonTrace/issues/9) | [#19](https://github.com/AI-Lab-G5/CarbonTrace/issues/19) |
| Backend / @felipecduque7 | [#11](https://github.com/AI-Lab-G5/CarbonTrace/issues/11) | [#21](https://github.com/AI-Lab-G5/CarbonTrace/issues/21) |
| DevOps + QA / @Bipelipe | [#13](https://github.com/AI-Lab-G5/CarbonTrace/issues/13) | [#24](https://github.com/AI-Lab-G5/CarbonTrace/issues/24) |

Sprint 2 (19 a 25/10) é S3 no guia; Sprint 3 (26/10 a 01/11) é S4. São 10 issues ativas, cinco por milestone; as anteriores foram consolidadas/adiadas como histórico, sem representar software concluído. J4/J5, revisão/cancelamento avançados, snapshot completo da rede e janela de idempotência de 24h continuam no planejamento posterior do MVP. Não antecipar deploy, Workload Identity ou pipeline completo de produção para o gate local.

## Diferenças observadas na base, ainda não resolvidas por documentação

A tabela resulta de leitura dos arquivos, não de uma nova execução da aplicação ou dos testes. As issues indicadas são responsáveis pela adequação e pela prova; nenhuma limitação passa a ser aceita como comportamento correto.

| Base observada | Alvo / continuidade |
| --- | --- |
| [auth.py](../backend/app/auth.py) usa cabeçalhos debug no modo emulator e os papéis leitor/operador/gestor | Token do Auth Emulator verificado, tenant/papel funcionario por rota; Backend #11/#21, DevOps #13, QA #24 |
| [firestore.rules](../firestore.rules) permite leitura pública de fatores e acesso direto de clientes do tenant | Deny-all para cliente anônimo/autenticado, API autoriza por conta própria; #13/#24 |
| [calculo.py](../backend/app/services/calculo.py) e modelos usam floats | Decimal no domínio e strings em transporte/persistência; #11/#21, revisão #7/#18 e prova #24 |
| [fatores-v1.json](dados/fatores-v1.json) inclui gás natural e resíduo de Escopo 3 | Adequar seed/catálogo às quatro fontes, manter preliminares identificados; #11/#13/#21 |
| [health.py](../backend/app/routers/health.py) publica /health | Alinhar /healthz e /readyz como exceções públicas; #7/#11/#18 |
| OpenAPI versionada em [docs/api](api/openapi.yaml) registra a base anterior | TL/Backend alinham contrato mínimo de J1-J3; a OpenAPI 0.2.0 em documentacao é alvo completo, não contrato gerado atual |
| CI da aplicação ainda não está versionado nesta base | #13 configura lint/build/testes reais; #18 comprova bloqueio de merge e revisão por outra pessoa |

## Evidências exigidas, ainda a produzir/validar

- [ ] J1-J3 do clique à API/Firestore Emulator e de volta, com recarga e dados persistidos; checkout limpo com Compose/configuração/seed sem ajustes manuais.
- [ ] Listas/formulários com carregando/vazio/erro, mensagens amigáveis, teclado, rótulos e status com texto e ícone além da cor.
- [ ] QA executa EP/BVA de zero/negativo/teto/unidade/mês, fronteiras abaixo/no/acima e resultado calculado à mão. TL/Backend definem o teto concreto antes da BVA; PO confere a regra.
- [ ] Quatro testes por rota protegida: sem token, expirado, papel errado e empresa errada; verificar também IDs externos e deny-all direto.
- [ ] QA produz /docs/rastreabilidade.md e /docs/relatorio-testes-v1.md com critérios/testes/resultados, versão, totais, cobertura e BUG-xxx. Bug Reports em /docs/bugs/BUG-xxx.md ligados à issue responsável; não criar mais issues apenas para guardar cada evidência.
- [ ] DevOps registra prints da calculadora de preços/faturamento em /docs/finops, premissas/data e gasto acumulado até US$ 5; PO confere. Excesso exige motivo/ações e apresentação ao tutor.
- [ ] PO registra revisões datadas S3/S4, testa pessoalmente, confere a matriz e prepara demo de 5 a 10 linhas incluindo erro. A revisão da S4 continua pendente até ocorrer.
- [ ] CI real verde e bloqueio de merge com falha comprovado, com PR revisado por outra pessoa; nenhum TODO ou teste pulado conta como aprovação.

Este documento é planejamento e registro de diferenças. Não substitui a matriz executada, o relatório de testes, os prints de custos nem o aceite do PO/tutor. No término da Sprint 2, registrar o progresso real e replanejar pendências sem retroagir conclusão.

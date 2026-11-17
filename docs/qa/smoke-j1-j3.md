# Smoke J1–J3 em checkout limpo

**Critério:** CA-08 da issue [#24](https://github.com/AI-Lab-G5/CarbonTrace/issues/24)
**Data da execução:** _preencher_
**Executado por:** _preencher_
**Revisão:** _preencher (commit)_
**Participantes:** _preencher (o guia pede PO + equipe)_

## Pré-requisitos

- Docker e Docker Compose
- Portas 3000, 8000, 8080 e 9099 livres
- Checkout limpo: `git status --short` vazio

## Roteiro (8 passos do registro do PO)

| # | Passo | Esperado | Obtido | Situação |
| --- | --- | --- | --- | --- |
| 1 | `git clone` + `docker compose up --build` | emuladores, catálogo e contas prontos sem ajuste manual | _preencher_ | _preencher_ |
| 2 | Login com `demo-a@carbontrace.local` / `carbontrace-demo` | entra como funcionário da empresa A | _preencher_ | _preencher_ |
| 3 | Cadastrar "Loja Centro" e vincular eletricidade | loja consultável na lista | _preencher_ | _preencher_ |
| 4 | Registrar 1 MWh de eletricidade para `2025-10` | quantidade original 1 MWh, convertida 1.000 kWh | _preencher_ | _preencher_ |
| 5 | Consultar o cálculo | 0,0385 × 1000 = **38,500 kgCO2e**, fator v1 identificado | _preencher_ | _preencher_ |
| 6 | Recarregar e consultar de novo | mesmo 38,500 com v1, mesmo com v2 no catálogo | _preencher_ | _preencher_ |
| 7 | Tentar consumo negativo e eletricidade em litros | erro amigável; nada gravado | _preencher_ | _preencher_ |
| 8 | Empresa B tenta abrir registro da empresa A pelo ID | recusa, sem revelar dados | _preencher_ | _preencher_ |

## Resultado

- Passos aprovados: _preencher_ / 8
- Passos reprovados: _preencher_
- Bloqueios encontrados: _preencher_

## Limitações

_registrar o que não pôde ser verificado e por quê_

## Prints de custo

Conferir `docs/finops/` antes de entregar ao PO: print do Firebase no plano **Spark** e
do Render no plano **free**, ambos sem forma de pagamento. Gasto acumulado ≤ US$ 5.

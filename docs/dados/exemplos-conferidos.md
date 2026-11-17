# Exemplos conferidos à mão

**Data:** 2026-10-27 · **Responsável:** Backend · Atende ao **CA-05** do Checkpoint 2.

Cada linha abaixo pode ser refeita numa calculadora comum. O propósito é esse:
se o número da API não bater com o da calculadora, o defeito é nosso, e esta
página é onde se descobre isso sem ler código.

Os valores foram gerados executando o próprio motor
(`backend/app/dominio/calculo.py`) sobre o catálogo real em
`docs/dados/fatores-v1.json` e `fatores-v2.json` - não foram digitados à parte.

> Os fatores estão marcados como `preliminar` no catálogo. Os números abaixo
> estão corretos *dado o fator*; a conferência dos fatores contra a fonte
> oficial (SEEG/GHG Protocol) é trabalho separado, registrado na ficha
> metodológica.

## A conta

```
emissão (kgCO2e) = quantidade convertida para a unidade base × fator da fonte
```

arredondada ao final para **3 casas decimais**, com `ROUND_HALF_EVEN`
(ver [ADR-009](../arquitetura/decisoes_adrs/0009-aritmetica-decimal-e-arredondamento.md)).

## Casos normais

| # | Fonte | Entrada | Versão | Convertido | Fator | Produto exato | **Resultado** | Escopo |
|---|---|---|---|---|---|---|---|---|
| 1 | Eletricidade | 1500 kWh | v1 (2025) | 1500 kWh | 0,0385 | 57,7500 | **57,750** | 2 |
| 2 | Eletricidade | 1500 kWh | v2 (2026) | 1500 kWh | 0,0426 | 63,9000 | **63,900** | 2 |
| 3 | Eletricidade | 2,5 MWh | v2 (2026) | 2500 kWh | 0,0426 | 106,50000 | **106,500** | 2 |
| 4 | Diesel | 350,5 L | v1 | 350,5 L | 2,6 | 911,30 | **911,300** | 1 |
| 5 | Gasolina | 1200 L | v1 | 1200 L | 2,21 | 2652,00 | **2652,000** | 1 |
| 6 | GLP | 190 kg | v1 | 190 kg | 2,93 | 556,70 | **556,700** | 1 |

**Casos 1 e 2** são a prova do CA-03 do lado do catálogo: a mesma quantidade,
em competências diferentes, usa fatores diferentes. Um lançamento de 2025
reaberto hoje continua valendo 57,750 - o fator vigente à época viaja gravado
junto do lançamento, não é consultado na hora da leitura.

**Caso 3** mostra a conversão de unidade acontecendo antes da multiplicação:
2,5 MWh viram 2500 kWh, e é sobre 2500 que o fator incide.

## Casos de arredondamento

O caso 7 contraria a regra que se aprende na escola, e alguém vai conferir à
mão e achar que encontrou um defeito. O caso 8 está ao lado dele de propósito:
mostra que a regra não é "sempre para baixo" - ela depende do dígito anterior.

| # | Entrada | Produto exato | Regra da escola | **Nosso resultado** |
|---|---|---|---|---|
| 7 | 1 kWh × 0,0385 | 0,0385 | 0,039 | **0,038** |
| 8 | 3 kWh × 0,0385 | 0,1155 | 0,116 | **0,116** |

Nos dois casos a quarta casa é exatamente 5 - um empate. `ROUND_HALF_EVEN`
desempata para o **dígito par**: no caso 7 o dígito anterior (8) já é par e o
valor fica; no caso 8 o anterior (5) é ímpar e sobe para 6.

Em um lançamento isolado a diferença é de um grama. Em um consolidado anual de
toda a rede, arredondar sempre para cima inflaria o total de forma
sistemática - e o total inflado é justamente o número que vai para o relatório
de inventário. Ambos os casos estão travados em
`backend/tests/test_dominio_calculo.py`.

## Casos recusados

Entrada que o sistema não aceita, e o que o usuário vê.

| Entrada | Resposta | Mensagem |
|---|---|---|
| quantidade `-5` | 422 | quantidade não pode ser negativa |
| 99.999.999 kWh de eletricidade | 422 | acima do teto mensal da fonte |
| 100 L de eletricidade | 422 | unidade incompatível; esperado kWh ou MWh |
| fonte `carvao_mineral` | 422 | não há fator publicado para a fonte |
| quantidade `1500.5` como número JSON | 422 | deve vir como texto, não como número decimal |
| competência `2026-13`, `2026/01`, `26-01` | 422 | formato inválido; esperado AAAA-MM |
| competência `2099-12` | 422 | competência no futuro |

**Zero não está nesta tabela de propósito.** `"quantidade": "0"` é um
lançamento válido e grava emissão `0.000`. "A loja não consumiu diesel em
março" é uma afirmação diferente de "ninguém lançou diesel em março": a
primeira fecha o inventário, a segunda deixa uma lacuna. Recusar zero
obrigaria o usuário a escolher entre inventar um número e deixar o mês em
branco (CA-03 da issue #11).

## Tetos por fonte

O teto é conferido **depois** da conversão de unidade, sempre na unidade base -
1001 MWh são comparados como 1.001.000 kWh, não como 1001.

| Fonte | Unidade base | Teto mensal |
|---|---|---|
| Eletricidade | kWh | 1.000.000 |
| Diesel | L | 200.000 |
| Gasolina | L | 100.000 |
| GLP | kg | 50.000 |

São filtros contra erro de digitação, não limites de negócio. Vêm do catálogo
de fatores e aparecem no contrato em `teto_mensal`, na resposta de
`GET /v1/fontes` - o front pode avisar antes de enviar. Mudam publicando uma
versão nova do catálogo, não alterando código.

A recusa do número decimal JSON costuma surpreender quem integra.
É intencional: `1500.5` em JSON já chega como ponto flutuante binário, e aceitá-lo
congelaria a imprecisão com aparência de exatidão. O formato correto é
`"quantidade": "1500.5"`, entre aspas.

## Como refazer a conferência

Com o repositório clonado:

```bash
cd backend
python -m pytest tests/test_dominio_calculo.py -v
```

Os 28 testes desse arquivo são estes mesmos casos, mais os limites de cada
faixa de validação.

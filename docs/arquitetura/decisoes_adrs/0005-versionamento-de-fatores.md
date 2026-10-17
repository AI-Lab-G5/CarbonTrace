# ADR-005 — Fatores de emissão imutáveis e versionados

**Status:** Aceito · **Data:** 2026-10-17 · **Autor:** Backend

## Contexto

O produto promete que uma rede consegue explicar, numa auditoria, de onde
veio cada número do inventário. Fatores de emissão, porém, mudam: o MCTI
republica o fator do SIN todo ano, e metodologias são revisadas.

Se os fatores forem simplesmente atualizados no lugar, um relatório emitido
em março deixa de bater consigo mesmo em dezembro. O auditor pergunta por que
o número mudou e ninguém consegue responder.

Esse é exatamente o problema que o cliente já tem hoje com planilhas. Repeti-lo
no sistema eliminaria a razão de ele existir.

## Decisão

Fatores ficam em `/fatores/{versao}`, numa coleção global, e **uma versão
publicada nunca é editada**. Corrigir um valor significa publicar uma versão nova.

Cada registro grava, junto do valor calculado, a versão e o valor exato do
fator aplicado:

```
fator_versao: "v1"
fator_valor: 0.0385
emissao_kg_co2e: 38.5
```

A versão vigente para uma competência é a mais recente cujo `vigencia_inicio`
seja menor ou igual a ela. Um lançamento de `2025-03` usa os fatores de 2025,
mesmo digitado em 2026.

## Consequências

**A favor.** Recalcular um período com o fator da época devolve exatamente o
mesmo número — é a cena da demo. A trilha de auditoria fica completa sem
estrutura adicional. E o cache em memória dos fatores é seguro por construção,
já que o conteúdo de uma versão nunca muda.

**Contra.** Redundância: o valor do fator fica repetido em todo registro. Para
o volume esperado (uma rede com dezenas de unidades, lançamentos mensais) isso
é irrelevante, e a alternativa — só guardar a versão — exigiria um join em toda
leitura.

Comparar dois períodos calculados com versões diferentes é legítimo mas precisa
ser sinalizado na interface, ou o usuário atribui a mudança ao consumo quando
ela veio do fator. **Fica como requisito para o frontend.**

Publicar versão nova é operação administrativa, fora do app. Ainda não há tela
para isso, e nesta fase é feito pelo script de seed.

## Alternativas descartadas

**Sobrescrever o fator.** Simples e errado: quebra a promessa central do produto.

**Guardar só a versão, sem o valor.** Economiza alguns bytes e cria uma
dependência de leitura em todo cálculo. Não compensa.

**Recalcular tudo a cada nova versão.** Faria os relatórios passados mudarem
sozinhos — o oposto do que uma auditoria precisa.

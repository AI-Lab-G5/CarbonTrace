# Ficha metodológica — cálculo de emissões

**Versão do dataset:** v1 · **Status:** rascunho · **Responsável:** Backend

---

## Aviso sobre os números

Os fatores do `fatores-v1.json` são **valores de partida para desenvolvimento**,
na ordem de grandeza correta, úteis para construir e testar o sistema. Eles
**ainda não foram conferidos na fonte oficial**.

Antes do Demo Day, cada fator precisa ser verificado e ter a citação completa
(documento, ano, tabela, página). Enquanto isso não acontece, o dataset fica
marcado como `"status": "rascunho"` e a interface deve exibir que os números
são preliminares.

Isso não é formalidade. O produto se vende como "auditável"; publicar número
sem procedência contradiz a própria proposta.

---

## Como a emissão é calculada

```
emissão (kgCO₂e) = quantidade consumida × fator da versão vigente
```

A fórmula é deliberadamente trivial. A confiabilidade do resultado **não vem
da matemática** — vem de saber exatamente qual fator foi aplicado, e quando.

## Escopos (GHG Protocol)

| Escopo | O que cobre | Exemplo na rede |
|---|---|---|
| **1** | Emissão direta, de fonte que a empresa controla | GLP da cozinha, diesel da frota própria |
| **2** | Emissão indireta da energia comprada | Eletricidade da rede |
| **3** | Demais emissões indiretas da cadeia | Resíduo enviado a aterro |

## Versionamento

Uma versão publicada **nunca é editada**. Corrigir um número significa
publicar uma versão nova.

Cada registro guarda a versão de fator usada no momento do lançamento. É o
que permite recalcular um período antigo com o fator da época e obter
exatamente o mesmo resultado — a cena prometida na demo.

Sem isso, um relatório emitido em março deixaria de bater consigo mesmo em
dezembro, e o sistema perderia a única coisa que o diferencia de uma planilha.

## Qual versão vale para cada competência

A versão vigente é a mais recente cujo `vigencia_inicio` seja menor ou igual
à competência do lançamento. Um registro de `2025-03` usa os fatores de 2025,
mesmo que seja digitado em 2026.

## Limitações conhecidas

1. **Fatores não verificados** — descrito acima.
2. **Fator de energia é média anual.** O MCTI publica fatores mensais; usar a
   média anual simplifica agora, mas reduz a precisão de comparações entre
   meses. Vale reavaliar.
3. **Sem conversão automática de unidades.** O lançamento precisa vir na mesma
   unidade do fator. Enviar m³ onde se espera kWh é aceito e produz número
   errado. É a falha mais provável do sistema hoje, e deveria virar validação.
4. **Escopo 3 incompleto.** Só resíduo. Transporte de carga, viagens e cadeia
   de fornecedores ficam de fora do MVP.

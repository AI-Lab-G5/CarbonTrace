# Ficha metodológica - cálculo de emissões

**Versão do dataset:** v1 · **Status:** rascunho · **Responsável:** Backend

---

## Aviso sobre os números

**Recorte aprovado em 25/10/2026:** eletricidade comprada (Escopo 2), diesel/gasolina de frota própria e GLP estacionário (Escopo 1). Eletricidade aceita kWh/MWh (1 MWh = 1000 kWh); diesel/gasolina L e GLP kg. Gás natural e resíduos presentes no dataset antigo não integram o catálogo aprovado; sua presença no arquivo não restabelece Escopo 3. O dataset e o seed não são modificados nesta revisão documental; a adequação fica nas issues #11/#13/#21.

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
emissão (kgCO₂e) = quantidade na unidade-base × fator da versão selecionada
```

No alvo aprovado, converter MWh para kWh antes de multiplicar; as demais fontes usam as unidades fixas do catálogo. O fator aplicado deve ser salvo com a entrada e o resultado, e a reprodução usa a versão original em vez de buscar a versão atual. Essa adequação continua pendente no motor atual, conforme as limitações abaixo.

A fórmula é deliberadamente trivial. A confiabilidade do resultado **não vem
da matemática** - vem de saber exatamente qual fator foi aplicado, e quando.

## Escopos (GHG Protocol)

| Escopo | O que cobre | Exemplo na rede |
|---|---|---|
| **1** | Emissão direta, de fonte que a empresa controla | GLP da cozinha, diesel da frota própria |
| **2** | Emissão indireta da energia comprada | Eletricidade da rede |
| **3, fora do MVP** | Demais emissões indiretas da cadeia | Resíduo enviado a aterro, presente apenas no dataset legado |

## Versionamento

Uma versão publicada **nunca é editada**. Corrigir um número significa
publicar uma versão nova.

Cada registro guarda a versão de fator usada no momento do lançamento. É o
que permite recalcular um período antigo com o fator da época e obter
exatamente o mesmo resultado - a cena prometida na demo.

Sem isso, um relatório emitido em março deixaria de bater consigo mesmo em
dezembro, prejudicando a rastreabilidade proposta. Isso não comprova uma vantagem exclusiva sobre planilhas ou concorrentes; a hipótese de diferenciação continua a validar.

## Qual versão vale para cada competência

A versão vigente é a mais recente cujo `vigencia_inicio` seja menor ou igual
à competência do lançamento. Um registro de `2025-03` usa os fatores de 2025,
mesmo que seja digitado em 2026.

## Limitações conhecidas

1. **Fatores não verificados** - descrito acima.
2. **Fator de energia é média anual.** O MCTI publica fatores mensais; usar a
   média anual simplifica agora, mas reduz a precisão de comparações entre
   meses. Vale reavaliar.
3. **Base anterior sem conversão automática de unidades.** O lançamento precisa vir na mesma
   unidade do fator. Enviar m³ onde se espera kWh é aceito e produz número
   errado. É a falha mais provável do sistema hoje, e deveria virar validação.
4. **Dataset fora do recorte vigente.** Gás natural e resíduo de aterro são legados, não fontes aprovadas; todo Escopo 3 está fora do MVP. Usar somente eletricidade, diesel, gasolina e GLP na entrega ajustada.
5. **Precisão/validação ainda a adequar.** O alvo exige Decimal/strings, ROUND_HALF_EVEN, zero explícito e rejeição de negativo/não finito/unidade ou mês inválidos e quantidade acima do teto definido por TL/Backend. QA testa as fronteiras e a equipe rotula fatores preliminares. As limitações listadas não são critérios aceitos como corretos.

# ADR-009 - Aritmética decimal e regra de arredondamento

**Status:** Aceito · **Data:** 2026-10-27 · **Autor:** Backend

Decisão tomada para a Jornada 3 (motor de cálculo), issue #21 do Checkpoint 2.

## Contexto

O CA-02 exige que o resultado do cálculo seja **conferível à mão**: o usuário
pega a quantidade, o fator, multiplica na calculadora e tem de encontrar
exatamente o número que a tela mostra. O CA-03 exige que o recálculo de um
lançamento antigo produza exatamente o mesmo valor de antes.

Ponto flutuante binário não atende nenhum dos dois. O caso é conhecido e vale
registrar porque é contraintuitivo:

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 1500 * 0.0385
57.74999999999999
```

O fator de eletricidade, 0,0385, não tem representação exata em binário - como
1/3 não tem em decimal. Multiplicado por 1500, o erro aparece na sexta casa. O
usuário que conferir na calculadora encontra 57,75 e a tela mostra outra coisa,
ou, pior, mostra 57,75 por arredondamento de exibição e soma 57,74999... no
consolidado. Num sistema que se vende como auditável, o número que fecha na
tela e não fecha na planilha é um defeito de confiança, não de precisão.

Há ainda uma particularidade do nosso armazenamento: o Firestore guarda número
como double de 64 bits. Gravar um valor exato ali o converteria em float na ida
ou na volta, desfazendo o cuidado tomado no cálculo.

## Decisão

**1. Todo número monetário ou de medição é `Decimal`, do início ao fim.**

Nenhum `float` existe no caminho entrada → cálculo → gravação → leitura →
resposta. A fronteira é `app/dominio/numeros.py`, que converte texto em
`Decimal` e **recusa `float` explicitamente**:

```python
if isinstance(valor, float):
    raise ValorNaoDecimal(
        f"{campo} deve vir como texto, nao como numero decimal."
    )
```

Recusar em vez de converter é deliberado. Um float que chega já chegou
impreciso: aceitá-lo e convertê-lo para `Decimal` apenas congelaria o erro com
aparência de exatidão. Melhor que o front descubra na primeira tentativa.

**2. Números trafegam e são armazenados como texto.**

No JSON, `"quantidade": "1500.5"`, não `1500.5`. No Firestore, string. Entrada
inteira (`1500`) é aceita porque inteiro em JSON é exato.

**3. Arredondamento: 3 casas decimais, `ROUND_HALF_EVEN`, uma única vez.**

Três casas em kgCO2e dão resolução de 1 grama - suficiente para o menor
lançamento plausível e já além da incerteza dos próprios fatores de emissão.

`ROUND_HALF_EVEN` (arredondamento bancário) desempata para o dígito par em vez
de sempre para cima. Em um consolidado de centenas de lançamentos, o
`ROUND_HALF_UP` enviesa o total para cima de forma sistemática; o half-even não
tem viés. É também o padrão da norma IEEE 754 e o default do módulo `decimal`.

Na prática, com o fator de eletricidade:

| Conta | Produto exato | Arredondado | Por quê |
|---|---|---|---|
| 1 kWh × 0,0385 | 0,0385 | **0,038** | empate; dígito anterior (8) já é par |
| 3 kWh × 0,0385 | 0,1155 | **0,116** | empate; dígito anterior (5) é ímpar, sobe |

Os dois casos estão fixados em `test_dominio_calculo.py`. Parecem
inconsistentes à primeira vista, e é exatamente por isso que precisam estar
documentados: quem conferir à mão com a regra da escola encontrará 0,039 no
primeiro caso.

**4. A ordem das operações é fixa: converter → conferir teto → multiplicar →
arredondar.**

```python
convertida = converter(quantidade, unidade_informada, fator.unidade_base)
if convertida > fator.teto:
    raise QuantidadeAcimaDoTeto(...)
emissao = arredondar_emissao(convertida * fator.valor)
```

Cada posição foi escolhida contra um erro concreto:

- **Arredondar por último.** Arredondar a quantidade convertida antes de
  multiplicar propagaria o erro multiplicado pelo fator, crescendo com o
  consumo.
- **Conferir o teto depois de converter.** Antes da conversão, 1001 MWh
  passaria por um teto de 1.000.000 kWh como se fossem 1001 kWh - três ordens
  de grandeza de folga indevida.
- **Somar valores já arredondados, não arredondar a soma.** O total do
  consolidado tem de bater com a soma das linhas que o usuário vê na tela. Um
  total que difere da soma das parcelas visíveis é o tipo de divergência que
  derruba a credibilidade de um relatório inteiro.

## Consequências

**A favor.** O número da tela é o número da calculadora. O recálculo de um
lançamento de 2025 devolve exatamente o valor original, o que torna o CA-03
verificável e não apenas declarado. O consolidado fecha com as parcelas.

**Contra.** `Decimal` é mais lento que `float` - irrelevante nesta escala, onde
o custo dominante é a ida ao Firestore. O front precisa tratar número como
string: não pode fazer `quantidade * 2` em JavaScript sem converter antes.
Vale o preço, porque o mesmo problema de precisão existe em JS e a string é a
única forma de atravessar a fronteira sem perda.

**Em aberto para o Tech Lead.** As três casas decimais e os tetos por fonte
(eletricidade 1.000.000 kWh; diesel 200.000 L; gasolina 100.000 L; GLP
50.000 kg) foram escolhidos pelo backend como valores de trabalho para
destravar a implementação. São ajustáveis sem mudança estrutural - o teto é
dado do catálogo de fatores, e a casa decimal é uma constante em
`numeros.py`.

## Alternativas descartadas

**`float` com arredondamento só na exibição.** É o desenho mais comum e o que
produz exatamente a falha do CA-02: o valor exibido arredonda certo, o valor
somado não.

**Inteiro em gramas (`57750` em vez de `57,750`).** Resolve a precisão e é
rápido. Descartado porque joga a conversão de unidade para a borda: todo
consumidor da API precisa lembrar de dividir por 1000, e quem esquecer erra por
três ordens de grandeza sem nenhum sinal.

**`ROUND_HALF_UP`.** Mais intuitivo para o usuário final, e seria defensável.
Descartado pelo viés acumulado em agregações, que é justamente o número que o
relatório de inventário publica.

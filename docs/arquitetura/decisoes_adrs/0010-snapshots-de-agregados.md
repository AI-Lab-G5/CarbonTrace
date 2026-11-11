# ADR-010 — Snapshots de agregados: quando são produzidos e como o reenvio não duplica

**Status:** Aceito · **Data:** 2026-11-11 · **Autor:** Backend

Decisão tomada para a Jornada 4 (issue #35, CA-03). O critério pede, em letra,
que esteja documentado **quando os agregados são produzidos** e **como
reenvios evitam duplicação** — é o que esta página responde.

## Contexto

O dashboard precisa de totais por unidade, região, mês e escopo. Há dois
jeitos de servi-los.

**Calcular na leitura** é o que o `/v1/consolidado` do CP2 faz: a cada abertura
da tela, varre todos os consumos da competência e soma. Funciona, e tem três
problemas que crescem juntos:

1. Uma rede de 30 lojas × 4 fontes × 12 meses são ~1.440 documentos lidos por
   abertura. No plano Spark, a cota de leitura acaba antes do mês.
2. O número muda debaixo do usuário. Duas pessoas olhando a mesma tela em
   momentos diferentes veem totais diferentes, e nenhuma das duas está errada.
3. Não existe "o total de janeiro publicado" — só "o total de janeiro agora".
   Um inventário auditável precisa do primeiro.

**Gravar na leitura** — calcular e salvar quando alguém abre a tela — resolve o
custo e cria um problema pior: um `GET` que escreve torna o custo imprevisível,
faz duas telas abertas disputarem o mesmo documento e viola o CA-03, que proíbe
consulta disparar escrita.

## Decisão

**1. Agregados são produzidos numa chamada de escrita explícita, e só nela.**

`POST /v1/snapshots` com a competência. É a única rota do módulo que grava.
Toda leitura — `GET /v1/snapshots`, `/v1/snapshots/{id}`, `/unidades`,
`/comparacao`, `/v1/agregados` — apenas lê. Nenhuma gera snapshot sob demanda,
nem quando não existe nenhum: nesse caso a resposta é **404 com a instrução de
gerar**, não uma geração silenciosa.

**2. Snapshot é imutável e versionado.**

O identificador é `{competencia}_v{NNN}` — legível, e ordenável como texto
(daí os zeros à esquerda: sem eles `v10` viria antes de `v2` e "a última
versão" seria a errada). Um snapshot nunca é editado nem apagado. Corrigir
lançamentos e gerar de novo cria `v002`; `v001` continua lá, com o número que
foi publicado na época.

É o que separa snapshot de cache: cache pode ser invalidado e regenerado sem
que ninguém note. Aqui, o histórico publicado não muda quando o dado de origem
muda — que é exatamente o que o CA-04 pede ao exigir "preservação de snapshots
anteriores".

**3. Reenvio sem mudança não duplica.**

Cada snapshot carrega a **impressão digital** do seu conteúdo: um SHA-256
(16 hex) sobre o total, cada unidade e cada região. Na geração:

| Situação | Resposta | O que acontece |
|---|---|---|
| Não existe snapshot da competência | **201** | Nasce a `v001` |
| Existe, e a impressão é a mesma | **200**, `criado: false` | Devolve o que já existe; nenhuma versão nova |
| Existe, e a impressão mudou | **201** | Nasce a versão seguinte; a anterior fica |

Duplo clique em "fechar o mês" não cria dois snapshots idênticos. E a
comparação é de **conteúdo**, não de tempo: não há janela de expiração para
alguém configurar errado, nem cabeçalho de idempotência que o cliente possa
esquecer de mandar. A garantia está no servidor.

**4. As linhas por unidade ficam em subcoleção.**

`/snapshots/{id}/unidades/{unidade_id}`, e não dentro do documento do snapshot.
Assim a listagem é paginável (CA-07) sem carregar a rede inteira, e o documento
do snapshot — que o dashboard lê primeiro — continua pequeno e barato.

A **posição no ranking vai gravada** em cada linha. A ordem não pode depender
de quem leu nem de como paginou: duas telas abertas lado a lado têm de mostrar
a mesma coisa.

**5. Região = UF.**

Enquanto a definição de região não vem do Tech Lead (#34), a UF é o único
recorte que já existe no cadastro e não exige migrar unidade nenhuma. Trocar
depois mexe só em quem monta o `Lancamento` em `services/snapshots.py` — o
domínio recebe a região pronta e não sabe de onde veio.

Unidade sem UF cadastrada não some do total: cai em `--`, visível na tela como
cadastro a corrigir. Sumir seria pior que aparecer errado.

## Consequências

**A favor.** Uma abertura de dashboard lê um documento mais uma página de
linhas, em vez de milhares de consumos. O total de uma competência passa a ser
um número publicado, com data, autor e versão — e isso é o que um auditor pede.
A igualdade entre os recortes é verificável, porque é verificada na geração.

**Contra.** O total só reflete os lançamentos até a última geração. Se alguém
lança um consumo e não gera snapshot, o dashboard mostra o número antigo —
corretamente, mas não o mais recente. A tela precisa exibir `gerado_em` e
oferecer o botão de gerar, senão o usuário não entende por que o número não
mudou. Isso é integração com o front (#36).

**Limitação registrada, para não passar por pronta.** O CA-06 define unidade
elegível como *ativa, com fonte esperada e coleta completa*. O cadastro não tem
o conceito de **fonte esperada** por unidade — sem ele, não há como distinguir
"não lançou" de "não tinha o que lançar". A elegibilidade implementada é
**ativa e com pelo menos uma fonte lançada**. Fechar essa lacuna depende do
contrato da #34; a aritmética do CA-06 (mediana, ranking, limiar de 50%) está
implementada e testada e não muda quando o campo chegar.

## Alternativas descartadas

**Agregação incremental a cada lançamento.** Atualizar os totais em transação,
a cada `PUT /v1/consumos`. Mantém tudo sempre atualizado e é o desenho certo
numa escala maior. Descartado aqui por duas razões: exige transação a cada
escrita (custo e complexidade que a rede deste tamanho não justifica) e não
produz o artefato que o CA-03 pede — um total *publicado*, com versão e data,
que não muda sozinho.

**Cloud Function agendada.** Gerar todo dia de madrugada. Boa ideia para
depois, e compatível com este desenho: a função chamaria a mesma geração. Fora
do CP3 porque o plano é custo zero e o agendamento é entrega de infraestrutura
(#37), não de backend.

**Recalcular na leitura com cache.** Junta o pior dos dois: continua sem
histórico publicado, e acrescenta invalidação de cache para errar.

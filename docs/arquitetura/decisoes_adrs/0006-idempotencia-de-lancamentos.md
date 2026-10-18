# ADR-006 — Idempotência dos lançamentos mensais

**Status:** Aceito · **Data:** 2026-10-17 · **Autor:** Backend

## Contexto

O lançamento mensal é feito por operadores nas lojas, muitas vezes do celular,
em conexão instável. O cenário previsível: a pessoa envia, a tela demora, ela
toca em "enviar" de novo.

Com `POST` criando documento novo a cada chamada, isso produz dois lançamentos
idênticos — e o consolidado da rede passa a contar o consumo em dobro. O erro
é silencioso: nada falha, só o número fica errado.

Numa plataforma que se vende como auditável, número inflado sem rastro é pior
que um erro visível.

## Decisão

O identificador do documento é **derivado dos dados**, não gerado aleatoriamente:

```
doc_id = f"{unidade_id}_{competencia}_{fonte_id}"
```

E a rota é `PUT /v1/registros`, não `POST`.

Uma unidade só pode ter um lançamento por fonte por competência — essa é a
regra de negócio real. Derivar o id dessa chave natural faz o reenvio
sobrescrever o registro em vez de duplicá-lo. A operação fica idempotente por
construção, sem tabela de controle, sem janela de expiração, sem cabeçalho
extra que o cliente possa esquecer de mandar.

`PUT` comunica exatamente isso: o mesmo pedido repetido leva ao mesmo estado.

## Consequências

**A favor.** Duplo clique deixa de ser problema. Reprocessar uma importação
inteira é seguro. E o cliente não precisa cooperar — a garantia está no
servidor.

**Contra.** Correção legítima e sobrescrita acidental ficam indistinguíveis: se
alguém lança 1000 kWh e depois 100 kWh por engano, o valor anterior se perde
sem registro.

Isso é aceitável agora e **não** será na Semana 4, quando entra a trilha de
auditoria. A solução prevista é manter o documento atual como está e gravar
cada alteração numa subcoleção `historico`, com autor e horário. O id
determinístico continua valendo; só deixa de ser a única cópia do dado.

Caracteres especiais em `unidade_id` ou `fonte_id` poderiam quebrar o id.
Ambos são gerados pelo sistema (Auto-ID do Firestore e slug do dataset de
fatores), então o risco é teórico — mas vale validar se um dia vierem de
entrada do usuário.

## Alternativas descartadas

**Cabeçalho `Idempotency-Key`.** Padrão de mercado (Stripe usa), mas exige que
o cliente gere e reenvie a chave. Depender do cliente para uma garantia do
servidor é frágil, e ainda precisaria de armazenamento das chaves com expiração.

**Deduplicar por consulta antes de gravar.** Consulta e gravação não são
atômicas; dois envios simultâneos passam pelos dois. Além de custar uma leitura
a mais em todo lançamento.

**Aceitar duplicatas e somar.** Deixaria o erro invisível, que é o pior caso.

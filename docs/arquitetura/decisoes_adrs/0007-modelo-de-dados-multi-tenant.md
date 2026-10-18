# ADR-007 — Modelo de dados e isolamento entre empresas

**Status:** Aceito · **Data:** 2026-10-17 · **Autor:** Backend

## Contexto

O CarbonTrace atende várias redes ao mesmo tempo. Dado da empresa A jamais pode
aparecer para a empresa B — não é preferência, é a condição para alguém
confiar dados de ESG a uma plataforma de terceiros.

No Firestore, vazamento entre clientes costuma vir de um lugar previsível:
coleção plana com campo `tenant_id`, e uma consulta em que o `where` foi
esquecido. A consulta funciona, não dá erro, e retorna tudo.

## Decisão

**O tenant vai no caminho, não num campo.**

```
/tenants/{tenantId}/unidades/{unidadeId}
/tenants/{tenantId}/registros/{registroId}
/fatores/{versao}                            ← global, somente leitura
```

Esquecer um `where` filtra demais e devolve vazio. Para vazar dado de outra
empresa seria preciso montar explicitamente o caminho dela — erro difícil de
cometer por distração.

**O `tenantId` vem da identidade, nunca do cliente.** Ele é lido de uma custom
claim do token do Firebase Auth, assinada pelo servidor. Nenhuma rota aceita
`tenant_id` como parâmetro. A função `colecao_do_tenant()` é o único caminho
para dados de cliente em todo o backend.

**Recurso de outra empresa devolve 404, não 403.** Distinguir "não existe" de
"existe mas não é seu" vazaria quais ids existem por aí.

## Consequências

**A favor.** O isolamento fica estrutural, não depende de disciplina em cada
consulta. As regras do Firestore ficam curtas, porque casam com o caminho. E
remover um cliente é apagar uma subárvore.

**Contra.** Consulta entre tenants fica inviável — qualquer métrica agregada
do produto exige varrer tenant por tenant. Aceitável: não há essa necessidade
no MVP, e quando houver, o caminho é exportar para BigQuery, não afrouxar o
modelo.

Índices compostos passam a ser por coleção. Para `registros`, filtrado por
competência e unidade, vai ser preciso declará-los em
`firestore.indexes.json` quando o volume crescer.

## Papéis (RBAC)

| Papel | Pode |
|---|---|
| `leitor` | Consultar unidades, registros e consolidado |
| `operador` | O acima, mais lançar e corrigir registros |
| `gestor` | O acima, mais criar e editar unidades |

O papel também vem de custom claim. A verificação acontece em dois lugares —
na API (`exige_escrita`) e nas regras do Firestore — porque uma delas é
contornável se alguém chamar o Firestore direto do navegador.

## Alternativas descartadas

**Coleção plana com `where("tenant_id", "==", ...)`.** Mais simples de escrever
e falha de forma perigosa: esquecer o filtro devolve tudo em vez de nada.

**Um projeto Firebase por cliente.** Isolamento perfeito e operação inviável —
cada novo cliente exigiria provisionar projeto, deploy e cota próprios.

**Firestore multi-tenancy nativo.** Existe para Firebase Auth, não para o
Firestore. Não se aplica.

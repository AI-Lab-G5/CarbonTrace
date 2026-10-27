# CarbonTrace - Backend

API de inventário de emissões de GEE. FastAPI + Cloud Firestore.

Versão **0.2.0** - Checkpoint 2, entrega das Jornadas 1, 2 e 3.

## Subir tudo

Pela raiz do repositório:

```bash
cp backend/.env.example backend/.env
docker compose -f infra/dev/docker-compose.yml up
```

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Documentação interativa | http://localhost:8000/docs |
| Emulator Suite | http://localhost:4000 |
| Frontend | http://localhost:3000 |

Com os containers no ar, carregue o catálogo de fatores e as unidades de
exemplo:

```bash
docker compose -f infra/dev/docker-compose.yml exec backend python scripts/seed.py
```

O seed publica **duas versões** de fatores (v1 vigente em 2025, v2 a partir de
2026-01) e cria `empresa-a` e `empresa-b`. As duas empresas existem de
propósito: com um tenant só, o isolamento nunca seria exercitado em
desenvolvimento.

## Autenticação

**Não há mais cabeçalho de debug.** Até o CP1 existia um `AUTH_MODE=emulator`
que aceitava `X-Debug-Uid` e `X-Debug-Tenant` sem assinatura. Foi removido:
uma porta de desenvolvimento que o deploy pode esquecer aberta é um risco
permanente, e não é preciso - o Auth Emulator emite ID token de verdade,
localmente.

Toda rota sob `/v1` exige:

```
Authorization: Bearer <id_token>
```

O token é verificado pelo SDK do Firebase. A identidade sai de duas custom
claims, **nunca** de algo enviado no corpo ou na query:

| Claim | Uso | Ausente ou inválida |
|---|---|---|
| `tenant_id` | define o caminho dos dados acessíveis | 403 |
| `papel` | precisa ser `funcionario` | 403 |

Sem token, 401. Token expirado, 401. O `tenant_id` vindo da claim é o que
monta o caminho `/tenants/{id}/...` - o isolamento vem da estrutura do
caminho, não de um filtro por campo que alguém possa esquecer de escrever.

Para obter um token no ambiente local, o front autentica contra o Auth
Emulator (`FIREBASE_AUTH_EMULATOR_HOST`); as claims são atribuídas pelo
DevOps na configuração do emulador (issue #13).

### Exceções públicas

`GET /healthz` e `GET /readyz` são as **únicas** rotas sem autenticação -
exceção acordada com o Tech Lead e registrada no CA-02 da issue #11.

O motivo: a sonda é chamada pelo orquestrador, que não tem token, e precisa
responder mesmo quando o Firebase Auth está fora do ar. Uma sonda que exigisse
token transformaria uma falha de autenticação em reinício em massa da
aplicação. Nenhuma das duas expõe dado de cliente - nem a mensagem do 503.

Os testes de autorização cobrem as duas pelo lado oposto: provam que respondem
sem token, o que impede alguém de "consertar" a lista de rotas protegidas
incluindo-as por engano.

## Rotas

| Método | Rota | Jornada |
|---|---|---|
| GET | `/healthz` | liveness - responde sem tocar em dependência |
| GET | `/readyz` | readiness - verifica o Firestore; 503 se ele não responde |
| GET POST | `/v1/unidades` | J1 - unidades da rede (GET paginado) |
| GET | `/v1/unidades/{id}` | J1 |
| GET | `/v1/fontes` | J1 - catálogo de fontes vigentes |
| GET | `/v1/fontes/versoes`, `/v1/fontes/versoes/{versao}` | J1 |
| GET PUT | `/v1/consumos` | J2 - lançamento mensal (GET paginado, PUT idempotente) |
| GET | `/v1/consumos/{id}` | J2 |
| POST | `/v1/consumos/{id}/recalculo` | J3 - prova do CA-03 |
| GET | `/v1/consolidado` | J3 - total e mediana da rede na competência |

Contrato completo em [`docs/api/openapi.yaml`](../docs/api/openapi.yaml),
gerado a partir do código:

```bash
python -c "import yaml, sys; sys.path.insert(0,'.'); from app.main import app; \
  yaml.safe_dump(app.openapi(), open('../docs/api/openapi.yaml','w'), \
  allow_unicode=True, sort_keys=False)"
```

## Números são texto

No JSON e no Firestore, toda quantidade e todo resultado trafegam como
**string**: `"quantidade": "1500.5"`, não `1500.5`.

Um número decimal em JSON chega como ponto flutuante binário e já chegou
impreciso - `1500 * 0.0385` dá `57.74999999999999` em float. A API **recusa**
float na entrada, com 422, em vez de converter: aceitar congelaria o erro com
aparência de exatidão.

O front precisa converter antes de fazer conta (`Number(x)` ou uma biblioteca
decimal). Razão completa em
[ADR-009](../docs/arquitetura/decisoes_adrs/0009-aritmetica-decimal-e-arredondamento.md),
e os valores conferidos à mão em
[`docs/dados/exemplos-conferidos.md`](../docs/dados/exemplos-conferidos.md).

## Testes

```bash
pytest           # suíte completa, 182 testes, sem dependência externa
ruff check .     # lint
```

Nada é pulado. Os testes de fluxo e de isolamento usam um dublê de Firestore
em memória (`tests/duble_firestore.py`), com banco limpo a cada teste - antes
dependiam do emulador e, sem ele, eram pulados, o que significava que nunca
rodavam na pipeline.

| Arquivo | O que prova |
|---|---|
| `test_dominio_numeros.py` | fronteira Decimal: float recusado, texto aceito |
| `test_dominio_competencia.py` | formato AAAA-MM, piso 2025-01, teto no mês corrente |
| `test_dominio_calculo.py` | a conta, a ordem das operações, o arredondamento |
| `test_autorizacao.py` | 11 rotas × 4 cenários: sem token, expirado, papel errado, empresa errada |
| `test_api_validacao.py` | entrada inválida barrada antes de chegar ao banco |
| `test_api_consumos.py` | fluxo HTTP → domínio → persistência → HTTP |
| `test_api_paginacao.py` | listas limitadas; percorrer tudo não repete nem pula item |
| `test_isolamento_tenant.py` | empresa B não lê, não lista e não escreve na empresa A |

A verificação de assinatura do token é substituída nos testes, por uma persona
num cabeçalho. É deliberado: conferir assinatura é código do Firebase, já
testado por eles; o que precisamos provar é a nossa autorização. A verificação
real, as regras do Firestore e os índices são exercitados contra o emulador
pelo QA, na issue #24.

## Estrutura

```
app/
├── main.py              aplicação e montagem das rotas
├── config.py            configuração vinda do ambiente
├── auth.py              verificação do token e identidade
├── db.py                cliente do Firestore e caminhos por tenant
├── models.py            contratos de entrada e saída
├── dominio/             regras puras, sem FastAPI e sem banco
│   ├── numeros.py       fronteira Decimal e arredondamento
│   ├── unidades.py      conversão entre unidades de medida
│   ├── competencia.py   validação de AAAA-MM
│   ├── calculo.py       o motor: calcular, recalcular, somar, mediana
│   └── erros.py         erros de domínio com mensagem para o usuário
├── routers/             uma rota por recurso
└── services/
    ├── fatores.py       leitura do catálogo versionado
    └── persistencia.py  tradução domínio ↔ documento do Firestore
```

`dominio/` não importa FastAPI nem Firestore. É o que permite testar a conta
sem subir nada - e o motivo de `test_dominio_calculo.py` rodar em
milissegundos.

## Listas são paginadas

`GET /v1/unidades` e `GET /v1/consumos` nunca devolvem tudo. A resposta é um
envelope:

```json
{
  "itens": [ ... ],
  "total_na_pagina": 50,
  "limite": 50,
  "proximo_cursor": "loja-asa-norte_2026-01_eletricidade"
}
```

`limite` tem padrão 50 e máximo 200. Para a próxima página, mande
`?cursor=<proximo_cursor>`. Quando `proximo_cursor` vem `null`, acabou - esse é
o único sinal de fim, e a última página nunca devolve cursor.

A paginação é por cursor e não por número de página porque o conjunto muda
enquanto alguém navega: um lançamento novo faz toda "página 3" seguinte repetir
ou pular item. O cursor marca onde parou. É também o que o Firestore cobra mais
barato - `offset` paga a leitura dos documentos que descarta.

Um cursor de outra empresa devolve 400: ele é resolvido sob o caminho de quem
chama, onde aquele documento não existe.

## Decisões registradas

Os números dos ADRs deste repositório são locais e não correspondem
automaticamente aos de `documentacao`.

- [ADR-005](../docs/arquitetura/decisoes_adrs/0005-versionamento-de-fatores.md) - fatores imutáveis e versionados
- [ADR-006](../docs/arquitetura/decisoes_adrs/0006-idempotencia-de-lancamentos.md) - idempotência dos lançamentos
- [ADR-007](../docs/arquitetura/decisoes_adrs/0007-modelo-de-dados-multi-tenant.md) - isolamento entre empresas
- [ADR-009](../docs/arquitetura/decisoes_adrs/0009-aritmetica-decimal-e-arredondamento.md) - aritmética decimal e arredondamento

## Dois detalhes que custam tempo quando esquecidos

O container sobe com `--host 0.0.0.0`. Dentro de um container, `127.0.0.1`
responde só a ele mesmo e a porta publicada no host não alcança nada.

O `.env` nunca vai para o Git - só o `.env.example`. O `.gitignore` já bloqueia
`.env` e qualquer JSON de conta de serviço.

# CarbonTrace - Backend

API de inventário de emissões de GEE. FastAPI + Cloud Firestore.

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

Com os containers no ar, carregue os fatores e dados de exemplo:

```bash
docker compose -f infra/dev/docker-compose.yml exec backend python scripts/seed.py
```

## Autenticação em desenvolvimento

**Base legada, ainda não aceite do CP2.** O exemplo abaixo descreve o código atual e não o login aprovado para a demo. O alvo é token Firebase/Auth Emulator verificado em cada rota protegida, claims tenant_id/papel=funcionario e apenas um perfil funcional; Backend implementa em #11/#21, DevOps configura em #13 e QA comprova em #24. Cabeçalhos debug e os papéis antigos não substituem os quatro testes de autorização por rota. Ver o [planejamento vigente](../docs/planejamento-checkpoint-2.md).

Com `AUTH_MODE=emulator`, a identidade vem de cabeçalhos:

```bash
curl http://localhost:8000/v1/unidades \
  -H "X-Debug-Uid: ana" \
  -H "X-Debug-Tenant: empresa-a" \
  -H "X-Debug-Papel: gestor"
```

Esse atalho só existe quando a variável está em `emulator`, e o valor é lido
do ambiente do servidor - nunca do pedido. Em `AUTH_MODE=firebase` a API exige
um ID token assinado, e o tenant vem de custom claim.

O seed cria `empresa-a` e `empresa-b` de propósito: com um tenant só, o
isolamento nunca seria exercitado.

## Testes

```bash
pytest                                              # unitários
FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 pytest       # inclui isolamento
ruff check .                                        # lint
```

Os testes de isolamento são **pulados** sem o emulador, em vez de falharem.
Uma execução sem emulador não comprova isolamento: testes pulados devem aparecer como pulados, nunca aprovados. Para o CP2, o ambiente/CI deve subir os emuladores e executar os casos reais; QA registra total, aprovados/reprovados/pulados, cobertura e BUG-xxx.

## Estrutura

```
app/
├── main.py              aplicação e montagem das rotas
├── config.py            configuração vinda do ambiente
├── auth.py              identidade e escopo de tenant
├── db.py                cliente do Firestore
├── models.py            contratos de entrada e saída
├── routers/             uma rota por recurso
└── services/
    ├── calculo.py       emissão e consolidação (funções puras)
    └── fatores.py       leitura dos fatores versionados
```

## Decisões registradas

Os números dos ADRs deste repositório são locais e não correspondem automaticamente aos números de documentacao. Foram contextualizados em 25/10; o [ADR-008 de produto](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/adr/ADR-008-recorte-crud.md) prevalece para o escopo futuro. A implementação do alvo continua pendente de evidências.

- [ADR-005](../docs/arquitetura/decisoes_adrs/0005-versionamento-de-fatores.md) - fatores imutáveis e versionados
- [ADR-006](../docs/arquitetura/decisoes_adrs/0006-idempotencia-de-lancamentos.md) - idempotência dos lançamentos
- [ADR-007](../docs/arquitetura/decisoes_adrs/0007-modelo-de-dados-multi-tenant.md) - isolamento entre empresas

## Dois detalhes que custam tempo quando esquecidos

O container sobe com `--host 0.0.0.0`. Dentro de um container, `127.0.0.1`
responde só a ele mesmo e a porta publicada no host não alcança nada.

O `.env` nunca vai para o Git - só o `.env.example`. O `.gitignore` já bloqueia
`.env` e qualquer JSON de conta de serviço.

# Deny-all das Security Rules — prova e resultado

Documento de apoio ao **CA-03** da issue #13 e ao **CA-04** da issue #24.

## O problema que este trabalho fecha

O backend tem 182 testes que exercitam a autorização da **API**. Nenhum deles
toca nas Security Rules do Firestore, por um motivo estrutural: a API usa o
**Admin SDK**, que ignora Rules por definição. Quem depende das Rules é o acesso
feito direto do cliente — e esse caminho nunca tinha sido testado.

Na prática, a segunda barreira existia no papel e não era verificada há três
checkpoints.

## Decisão: deny-all, sem exceção

A versão anterior das Rules permitia duas coisas ao cliente:

| Regra anterior | Por que caiu |
| --- | --- |
| `match /fatores/{versao}` leitura pública | O frontend **não lê fatores direto** — usa `GET /v1/fontes`. Porta aberta sem uso é superfície de ataque de graça. |
| `match /tenants/{tenantId}/**` por claim | Duplicava a autorização que a API já faz. Duas fontes de verdade sobre permissão divergem com o tempo, e a divergência é onde o vazamento aparece. |

A verificação foi feita no código do frontend: não há uma única chamada ao
Firestore cliente. Só o Auth é usado no navegador, e o Auth não passa por estas
regras.

Resultado — a regra inteira:

## O que o teste prova

`qa/test_deny_all.py`, nove casos:

| Caso | O que exige |
| --- | --- |
| Anônimo não lê | 403 em `GET /tenants/empresa-a/unidades` |
| Anônimo não escreve | 403 em `PATCH` no mesmo caminho |
| Anônimo não apaga | 403 em `DELETE` |
| **Autenticado não lê** | 403 mesmo com ID token legítimo da empresa certa |
| **Autenticado não escreve** | 403 |
| Empresa B tentando ler A | 403 |
| Fatores direto | 403 (fecha a exceção antiga) |
| Admin SDK continua funcionando | grava e apaga sem erro |
| API responde com dado semeado | 200 em `GET /v1/unidades` |

O quarto caso é o coração do deny-all: não basta barrar desconhecido. O
funcionário autenticado da empresa A **também** não fala direto com o banco —
todo acesso passa pela API, que é auditável.

O oitavo caso é a rede de proteção contrária: um deny-all mal feito, que
barrasse o Admin SDK, derrubaria o produto inteiro. O teste falha se isso
acontecer.

Token de verdade, não dicionário de claims: as Rules leem `request.auth`, que o
emulador monta a partir do token assinado. Um dicionário forjado não percorreria
esse caminho e o teste aprovaria algo que não existe.

## Como executar

Com o ambiente no ar (`docker compose up`), na raiz do repositório:

```bash
python -m pytest qa/test_deny_all.py -v

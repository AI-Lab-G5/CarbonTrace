# Frontend J1–J3: implementação e evidências

Branch: `feat/front-integracao-j1-j3`. Esta revisão substitui o diagnóstico inicial
que registrava Docker indisponível e ausência de E2E. O fluxo suportado pela API foi
executado com Auth Emulator, Firestore Emulator e backend reais, sem mocks no E2E.
O aceite integral das issues permanece dependente das lacunas de backend e da revisão da equipe.

## Resultado da validação

| Verificação | Resultado |
|---|---|
| `npm test` em frontend | 13 aprovados: 2 decimais + 11 Vitest |
| `npm run lint` | Aprovado, sem warnings |
| Build TypeScript/Vite e imagem Docker | Aprovados |
| `npx playwright test` em frontend | 2 E2E aprovados, última execução 46 segundos |
| `git diff --check` | Aprovado |
| Healthcheck do frontend | healthy após correção de localhost para 127.0.0.1 |
| Revisão visual | Login e jornada inspecionados em desktop e celular de 390 px; sem overflow horizontal |
| CI remoto / revisão independente / aceite PO | Não executados ou concedidos nesta sessão |

Vitest usa dublês para isolar componentes/HTTP. Playwright provisiona contas temporárias
com senha aleatória em memória e autentica pela interface real. Tokens não são gravados
em evidências. O ensaio usou o checkout de trabalho com build Docker, não foi repetido
em clone limpo separado.

### Cenários comprovados

- Login e logout individuais; cadastro e consulta das lojas da empresa.
- Quantidade negativa recusada pela interface e pela API (422); registro salvo preservado.
- 1 MWh em 2025-10: conversão para 1.000 kWh, fator preliminar v1 0.0385,
  emissão JSON `38.500`, apresentada como **38,500 kgCO2e**.
- Recarga recupera consumo pela API. Reprodução usa v1 mesmo com v2 no catálogo.
- Troca para empresa B remove dados de A; GET do consumo de A com token de B retorna 404.
- Backend interrompido no projeto de teste: mensagem de indisponibilidade; após reinício,
  botão de nova tentativa recupera prontidão. O teste restaura o backend em finally.
- Teclado no login, campos rotulados, estados de catálogo, erro 401, erro de campo 422,
  resposta não JSON, cancelamento, falha de rede e ausência de retry automático de escrita.
- Formatação decimal HALF_EVEN, zero explícito, rejeição de vazio/negativo/não finito.

## Capturas inspecionadas

- [Login desktop](evidencias/login-desktop.png)
- [Login celular](evidencias/login-mobile.png)
- [Jornada desktop](evidencias/jornada-desktop.png)
- [Jornada celular](evidencias/jornada-mobile.png)

As capturas do login incluem API indisponível durante a preparação; as da jornada
mostram resultado persistido e API pronta. Identidades/lojas são sintéticas. A revisão
visual corrigiu o banner flutuante do SDK que cobria conteúdo no celular. A identificação
de ambiente local passou para o formulário. Os selects receberam nomes acessíveis explícitos.

## Rastreabilidade #9

| CA | Evidência frontend | Limite do aceite |
|---|---|---|
| 01 | E2E login/logout com ID token real; teste 401 e teclado | Expiração real de token e matriz de autorização completa ficam com QA |
| 02 | E2E cadastro/lista/consulta; catálogo por competência | Código único e fontes vinculadas por loja ausentes no backend |
| 03 | Decimais testados; E2E negativo/422 sem alterar salvo | Tetos/faixa de datas requerem decisão TL/PO e fronteiras QA |
| 04 | Componentes de loading/vazio/erro; E2E indisponibilidade e recuperação | Cobertura não é exaustiva de todas as falhas possíveis |
| 05 | Labels, foco, teclado no login, revisão desktop/celular | Não constitui auditoria completa de acessibilidade |
| 06 | E2E cadastro → gravação → consulta → recarga | Vínculo de fonte permanece pendente no contrato |

## Rastreabilidade #19

| CA | Evidência frontend | Limite do aceite |
|---|---|---|
| 01 | E2E resultado, conversão, v1 e status preliminar | Autoria/datas não fornecidas pelo backend |
| 02 | E2E com API/Auth/Firestore reais e recarga | Clone limpo separado não repetido; preparação explícita abaixo |
| 03 | Testes de erro e dois E2E; healthz/readyz e timeout | Matriz formal fica com QA |
| 04 | Decimal textual, HALF_EVEN de apresentação, labels e visual | Auditoria ampla de acessibilidade não executada |
| 05 | 1.000 × 0.0385 = 38.500 conferido independentemente; recálculo com v1 | Conferência conjunta Backend/QA e decisão de precisão pendentes |
| 06 | Este relatório, testes e capturas preparados para revisão | Envio, revisão independente e aceite PO não realizados |

## Ambiente e reprodução

Docker Desktop estava instalado em `%LOCALAPPDATA%/Programs/DockerDesktop`, diferente
do caminho padrão tentado inicialmente. Iniciar esse executável disponibilizou o engine.
Containers Supabase de outro projeto foram preservados. Projeto dedicado: `carbontrace-front-test`.
O override fixa `--project demo-carbontrace` no emulador e GCLOUD_PROJECT/GOOGLE_CLOUD_PROJECT
no backend, para resolver a configuração do Admin SDK sem mudar autenticação ou contrato.

Na raiz:

```powershell
docker compose -p carbontrace-front-test -f docker-compose.yml -f compose.frontend-test.yml up --build -d
docker compose -p carbontrace-front-test -f docker-compose.yml -f compose.frontend-test.yml exec -T backend python scripts/seed.py
```

O primeiro build baixa ferramentas e imagens. Se o healthcheck expirar durante a primeira
preparação mas o emulador ficar saudável depois, repetir `up -d`. A carga de fatores
é explícita; o seed atual pode substituir a mesma versão e é restrito ao ambiente de teste.

Em frontend:

```powershell
npm ci
npm test
npm run lint
npm run build
npx playwright install chromium
npx playwright test
```

Playwright usa `http://127.0.0.1:3000`, provisiona contas somente no projeto de teste e
interrompe/reinicia apenas seu backend no cenário de indisponibilidade. Mantém os dados
sintéticos para inspeção. Para encerrar somente este ambiente, executar na raiz:

```powershell
docker compose -p carbontrace-front-test -f docker-compose.yml -f compose.frontend-test.yml down
```

## Pendências externas e riscos conhecidos

- Backend #11/#21: código de negócio único, vínculo de fontes por loja, autoria/datas,
  criação atômica com 409 e preservação do registro. A verificação preventiva do frontend
  não elimina concorrência; não há tela de edição destrutiva ou histórico fictício.
- DevOps/QA #13/#24: Rules deny-all e testes diretos completos. Rules permissivas não foram
  alteradas. O 404 entre empresas comprovado no E2E não substitui quatro negações por rota.
- TL/PO: tetos, faixa de competência e arredondamento por lançamento versus soma exata.
- QA produz matriz/relatório formais; PO confere e aceita; revisão independente e CI remoto
  continuam necessários. Nenhuma issue foi fechada nem houve push.
- npm reportou 16 vulnerabilidades (12 moderadas, 4 altas); triagem de dependências pendente,
  sem upgrades forçados nesta entrega. O relatório não certifica segurança global.

Falhas intermediárias foram corrigidas/retestadas: espera por seletor no primeiro E2E,
consulta inicial concorrente ao cadastro, ausência de timeout nas sondas e healthcheck
IPv6. Os resultados aprovados acima são das execuções finais; falhas anteriores não
foram contadas como sucesso.

## Commits da implementação

```text
4a3b980 fix(frontend): limitar espera das sondas da API
f412972 fix(frontend): usar IPv4 no healthcheck do Nginx
3f226b0 fix(frontend): explicitar nomes acessíveis dos seletores
29c87ed fix(frontend): aguardar consulta inicial antes de cadastrar
0389d0c fix(frontend): manter aviso local sem sobrepor formulário móvel
0e82a4a fix(frontend): preservar lojas paginadas ao mudar competência
02004e2 fix(frontend): rejeitar respostas inválidas de sucesso do proxy
76a47ef chore(frontend): alinhar projeto Firebase no ambiente de integração
3486857 test(frontend): cobrir transporte HTTP e jornadas com componentes
c0eb955 fix(frontend): distinguir estados do catálogo e validar medidas
32b3431 docs(frontend): registrar critérios parciais e bloqueios reais
b6d1c48 docs(frontend): documentar configuração da integração local
ff778fc ci(frontend): executar testes decimais junto do lint
a1ee04e fix(frontend): impedir troca de contexto durante operações
e53bf12 fix(frontend): distinguir saúde e prontidão do backend
59d16b6 test(frontend): validar decimais e configurar Firebase SDK
352d264 feat(frontend): conectar unidades coleta e resultados à API
be37933 feat(frontend): preparar login individual no Auth Emulator
791445b feat(frontend): validar e apresentar decimais sem ponto flutuante
e7eab83 feat(frontend): centralizar transporte autenticado e erros HTTP
21cbb74 fix(frontend): consultar a sonda healthz implementada
507daf5 refactor(frontend): definir tipos do contrato real
```

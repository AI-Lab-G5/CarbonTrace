# CarbonTrace - Frontend

Interface web para estimativa, inventário e gestão de emissões de gases de efeito estufa (GEE) para redes de varejo.

## Visão Geral

O frontend organiza o inventário em duas áreas autenticadas: unidades da empresa e coleta mensal de consumos. Usa React, TypeScript e React Router, com a identidade escura e verde do CarbonTrace. O Nginx serve os arquivos estáticos e encaminha as chamadas da API.

### Recursos da interface atual

- **Navegação:** rotas de unidades e consumos, indicação da página ativa, histórico do navegador e acesso direto por URL.
- **Acesso protegido:** restauração da sessão, login, verificação de vínculo à empresa e retorno à rota solicitada após concluir o acesso.
- **Unidades:** cards com cidade/UF, cadastro, consulta e atalho para registrar consumo na loja selecionada.
- **Coleta mensal:** escolha de loja/competência, fontes e medidas compatíveis, histórico paginado e consulta do resultado salvo.
- **Rastreabilidade:** quantidade original, conversão, emissão, fator versionado e conferência do cálculo original pela API.
- **Movimento:** entrada de telas e campos, carregamento com skeletons, destaque de cadastros e confirmação das ações. A preferência `prefers-reduced-motion` desativa animações e transições.
- **Responsividade e teclado:** menu lateral em desktop, navegação horizontal em telas menores, foco na mudança de rota e atalho para o conteúdo.
- **Conexão:** painel recolhível de integridade, aberto automaticamente em caso de erro, com nova tentativa.

### Componentes históricos fora do fluxo principal

Os componentes de calculadora didática e apresentação permanecem no repositório, mas não são montados no fluxo integrado:

- **Calculadora Didática de Emissões:** Estimativa instantânea de emissões em kg CO₂e/mês baseada em consumo de energia elétrica (kWh), combustível de frota (litros de diesel) e resíduos encaminhados a aterro (kg).
- **Breakdown Gráfico:** Visualização percentual proporcional por fonte emissora com barras de progresso animadas.

---

## Stack Tecnológica

- **Framework:** React 19 + TypeScript
- **Bundler / Dev Server:** Vite 8
- **Linter:** ESLint 10 (com verificação rigorosa `--max-warnings 0`)
- **Servidor de Produção / Container:** Nginx 1.27 Alpine com proxy reverso para `/api`

---

## Rotas e organização

| Endereço | Tela / comportamento |
| --- | --- |
| `/` | Encaminha para a área correspondente ao estado da sessão |
| `/entrar` | Login, criação de conta e recuperação de acesso |
| `/acesso` | Verificação de e-mail e vínculo por convite |
| `/unidades` | Cadastro e consulta de lojas; exige acesso autorizado |
| `/consumos` | Coleta, histórico e resultado; exige acesso autorizado |
| Outros endereços | Página não encontrada com retorno ao início |

O roteamento usa o [modo declarativo do React Router](https://reactrouter.com/start/declarative/routing). `App.tsx` mantém a máquina de estados da sessão e controla o acesso às rotas. `Jornadas.tsx` é o layout persistente das duas áreas autenticadas, com navegação e `Outlet`.

`hooks/useJornadas.ts` concentra as chamadas existentes à API e os estados compartilhados. `pages/UnidadesPage.tsx` e `pages/ConsumosPage.tsx` apresentam cada jornada. Os filtros e o rascunho de consumo permanecem ao trocar de rota; uma recarga inicia um formulário novo e consulta os dados persistidos pela API.

O cálculo continua no backend, com decimais textuais, prevenção de gravação duplicada e fatores versionados. Os contadores da interface indicam itens **carregados**, sem assumir o total de todas as páginas. As fontes continuam limitadas a eletricidade, diesel, gasolina e GLP. Dashboard, ranking e exportação ficam para as próximas etapas.

O fallback SPA já está configurado em `nginx.conf` para permitir recarga em `/unidades` e `/consumos`.

## Como rodar

### 1. Desenvolvimento local

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor Vite (com proxy para http://localhost:8000)
npm run dev
```

### 2. Lint e Build

```bash
# Executar ESLint
npm run lint

# Executar checagem de tipos (tsc) e build de produção do Vite
npm run build
```

### 3. Container Docker

```bash
docker build -t carbontrace-frontend .
```


## Integração J1–J3

A interface principal usa Firebase Auth Emulator e as rotas `/api/v1` do backend.
Execute `npm ci`, `npm test`, `npm run lint`, `npm run build` e `npm run dev`.
Use contas provisionadas pela equipe com claims `tenant_id` e `papel=funcionario`.
O projeto padrão é `demo-carbontrace` e o Auth Emulator é acessado pelo navegador em
`http://127.0.0.1:9099`. Confira `.env.example`. As variáveis VITE_* são de build;
para customizar o container, forneça a configuração ao build e reconstrua a imagem.
Os defaults locais permitem o build padrão do Compose sem credenciais de produção.
Health e readiness são consultados em `/api/healthz` e `/api/readyz`.

A calculadora didática deixou de ser a tela principal. Consumos e resultados são
consultados pela API após recarga. A documentação anterior de calculadora descreve
a base histórica, não o fluxo integrado atual.

Veja `docs/frontend/entrega-j1-j3.md` na raiz para validações e bloqueios.


### Testes de componentes e ponta a ponta

`npm test` executa testes decimais e Vitest/Testing Library. Para a integração real,
suba o Compose com `compose.frontend-test.yml`, execute o seed e rode, em frontend,
`npx playwright install chromium` e `npx playwright test`. O E2E cria contas sintéticas
e para/reinicia somente o backend do projeto `carbontrace-front-test` em um cenário.
As instruções completas e limites estão no relatório de entrega da raiz.

### Testes da navegação e da interface sem Docker

```bash
npx playwright install chromium
npm run test:ui
```

`playwright.ui.config.ts` inicia um Vite isolado na porta 3100 e executa `e2e/ui.spec.ts`, com respostas simuladas para Firebase Auth e API. Os cenários cobrem rota protegida e retorno após login, voltar/avançar, preservação do rascunho, recarga, logout, validação decimal, cadastro, consulta do fator original, falha de conexão, layout a 390 px e movimento reduzido. Capturas desktop/mobile ficam em `test-results/`.

O comando `npx playwright test` mantém a suíte `e2e/real.spec.ts`, que exige o ambiente Compose e exercita a integração real; as respostas simuladas não comprovam persistência ou isolamento no backend.

Validação local em 02/11/2026: lint e build aprovados, 2 testes decimais e 40 testes de componentes/API aprovados, além de 3 cenários de navegador com serviços simulados. Capturas desktop e mobile foram inspecionadas. A suíte de integração real não foi executada nesta validação porque o Docker Engine estava indisponível.

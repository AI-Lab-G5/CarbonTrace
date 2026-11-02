# CarbonTrace - Frontend

Interface web para estimativa, inventário e gestão de emissões de gases de efeito estufa (GEE) para redes de varejo.

## Visão Geral

O frontend adota a identidade visual e o modelo funcional da calculadora **Pegada Rede / CarbonTrace**, servido via Nginx com proxy reverso e construído com componentes modernos e tipados em TypeScript.

### Principais Recursos
- **Calculadora Didática de Emissões:** Estimativa instantânea de emissões em kg CO₂e/mês baseada em consumo de energia elétrica (kWh), combustível de frota (litros de diesel) e resíduos encaminhados a aterro (kg).
- **Breakdown Gráfico:** Visualização percentual proporcional por fonte emissora com barras de progresso animadas.
- **Painel de Integridade da API:** Monitoramento em tempo real do endpoint `/api/health` com indicação de status (loading, online, indisponível) e mecanismo de nova tentativa.
- **Servidor Nginx Otimizado:** Imagem Alpine com gzip, cache agressivo para assets estáticos, `server_tokens off` e fallback SPA.

---

## Stack Tecnológica

- **Framework:** React 19 + TypeScript
- **Bundler / Dev Server:** Vite 8
- **Linter:** ESLint 10 (com verificação rigorosa `--max-warnings 0`)
- **Servidor de Produção / Container:** Nginx 1.27 Alpine com proxy reverso para `/api`

---

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

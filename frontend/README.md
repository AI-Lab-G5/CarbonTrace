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

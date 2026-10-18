# CarbonTrace — Frontend

Interface web para acompanhamento e gestão do inventário de emissões de GEE.

## Stack

- **Framework:** React 19 + TypeScript
- **Bundler / Dev Server:** Vite 8
- **Linter:** ESLint 10 (com verificação rigorosa `--max-warnings 0`)
- **Servidor de Produção / Container:** Nginx Alpine (proxy reverso para `/api`)

## Como rodar

### 1. Desenvolvimento local

```bash
# Instalar dependências
npm install

# Iniciar servidor Vite (com proxy para http://localhost:8000)
npm run dev
```

### 2. Lint e Build

```bash
# Executar ESLint
npm run lint

# Executar checagem de tipos (tsc) e build do Vite
npm run build
```

### 3. Container Docker

O Dockerfile do frontend utiliza build multi-stage (Node 22 para build e Nginx Alpine para servir estáticos e rotear `/api/` para o container do backend).

```bash
docker build -t carbontrace-frontend .
```

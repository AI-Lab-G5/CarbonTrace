# CarbonTrace

Plataforma de inventário e gestão de emissões de gases de efeito estufa (GEE).

## Stack e Serviços

- **Frontend:** React + TypeScript + Vite + Nginx
- **Backend:** FastAPI + Python 3.12 (`backend/`)
- **Emuladores:** Firebase Auth e Cloud Firestore (`infra/emulator/`)

---

## Frontend

O frontend da aplicação está localizado no diretório `frontend/`.

### Rodar via Docker Compose (recomendado)

Pela raiz do repositório:

```bash
# 1. Garanta que o arquivo de variáveis do backend existe
cp backend/.env.example backend/.env

# 2. Suba todos os serviços (emuladores, backend e frontend)
docker compose up --build
```

Acesse:
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Documentação da API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Firebase Emulator Suite:** [http://localhost:4000](http://localhost:4000)

O Nginx no container do frontend atua como proxy reverso para `/api/*`, encaminhando as requisições internamente para o serviço `backend:8000` sem problemas de CORS ou URLs hardcoded no cliente.

### Rodar Localmente em Desenvolvimento

Para rodar o frontend no ambiente de desenvolvimento local usando o Vite:

```bash
cd frontend

# 1. Instalar dependências
npm install

# 2. (Opcional) Configurar variáveis de ambiente
cp .env.example .env

# 3. Iniciar o servidor de desenvolvimento
npm run dev
```

O Vite subirá em [http://localhost:3000](http://localhost:3000) com proxy reverso transparente configurado para redirecionar chamadas de `/api` para `http://localhost:8000`.

### Lint e Build

No diretório `frontend/`:

```bash
# Verificação estática de código (zero warnings tolerados)
npm run lint

# Checagem de tipos (tsc) e build de produção (vite)
npm run build
```

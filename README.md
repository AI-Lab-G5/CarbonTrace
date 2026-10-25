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

## Escopo e planejamento vigentes (25/10/2026)

O alvo aprovado é um CRUD de consumos para um único perfil funcionario, com login individual e acesso às unidades da própria empresa. Fontes: eletricidade, diesel, gasolina e GLP; eletricidade kWh/MWh, diesel/gasolina L e GLP kg. Gás natural e resíduos/Escopo 3 presentes no seed antigo não fazem parte do catálogo aprovado.

O CP2 de 01/11 cobre J1 cadastro de unidades/fontes, J2 coleta mensal validada e J3 cálculo com fatores versionados, localmente. São 10 issues ativas, cinco por sprint e uma por integrante. J4/J5 (dashboard/ranking/mediana e PDF/CSV) continuam no MVP para as etapas seguintes. Revisões concorrentes, cancelamento avançado, snapshots completos da rede e idempotência de 24h não bloqueiam este gate.

O código desta base ainda contém atalhos e decisões anteriores. Este texto não declara o CP2 entregue: papéis antigos/cabeçalhos debug, floats, seed com fontes excluídas e Rules permissivas precisam de adequação pelas issues existentes. Não usar a documentação ou os testes já existentes como prova automática do recorte novo.

Ver [distribuição e diferenças observadas](docs/planejamento-checkpoint-2.md), [decisão de produto](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/adr/ADR-008-recorte-crud.md) e [backlog completo](https://github.com/AI-Lab-G5/documentacao/blob/main/docs/backlog/MoSCoW.md). A OpenAPI de docs/api/openapi.yaml deste repositório descreve a base anterior; o contrato-alvo 0.2.0 está em documentacao e não comprova compatibilidade do código atual.

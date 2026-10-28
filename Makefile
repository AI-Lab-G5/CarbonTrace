# Makefile - raiz do repo. Responsável: DevOps.
COMPOSE = docker compose -f docker-compose.yml --project-directory .

setup:
	@test -f backend/.env  || cp backend/.env.example backend/.env
	@test -f frontend/.env || cp frontend/.env.example frontend/.env

up: 
	docker compose up --build

down:
	docker compose down

ps:
	docker compose ps

psa:
	docker compose ps -a

# Backend: lint e testes unitários (os de emulador pulam sem FIRESTORE_EMULATOR_HOST)

test: 
	cd backend && pytest

lint-backend:
	cd backend && ruff check .

# Contrato OpenAPI: normaliza e valida (mesma sequência do CI)
docs-lint:
	python3 scripts/patch_openapi.py
	npx --yes @redocly/cli lint docs/api/openapi.yaml

.PHONY: setup up down ps psa test lint-backend docs-lint

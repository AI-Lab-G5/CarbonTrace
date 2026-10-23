COMPOSE = docker compose -f infra/dev/docker-compose.yml --project-directory .

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


.PHONY: docks-lint
docs-lint:
	python3 scripts/patch_openapi.py
	npx --yes @redocly/cli lint docs/api/openapi.yaml

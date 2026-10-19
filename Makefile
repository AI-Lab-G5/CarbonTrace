# Makefile
setup:
	@test -f backend/.env  || cp backend/.env.example backend/.env
	@test -f frontend/.env || cp frontend/.env.example frontend/.env

up: setup
	docker compose up --build

down:
	docker compose down

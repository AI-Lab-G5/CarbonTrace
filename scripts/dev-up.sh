#!/usr/bin/env bash
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  echo "✔ .env criado a partir do .env.example"
fi

docker compose up --build "$@"


#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../docker"
[ -f .env ] || cp .env.example .env
docker compose up -d --build
docker compose ps
echo "Logs: docker compose logs -f"

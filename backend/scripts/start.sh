#!/usr/bin/env bash
set -e

echo "==> Применяю миграции (alembic upgrade head)"
alembic upgrade head

echo "==> Запускаю API (uvicorn)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

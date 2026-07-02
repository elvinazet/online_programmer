#!/usr/bin/env bash
# Сборка sandbox-образов для judge. Запускать на docker-хосте, где крутится worker.
set -e
cd "$(dirname "$0")"
docker build -t op-sandbox-python -f Dockerfile.python .
docker build -t op-sandbox-cpp -f Dockerfile.cpp .
echo "Готово: op-sandbox-python, op-sandbox-cpp"

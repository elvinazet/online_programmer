#!/bin/sh
# Entrypoint sandbox для Python. Исходник — в SRC_B64, тест — на stdin.
set -e
echo "$SRC_B64" | base64 -d > /work/main.py

# "Компиляция" = проверка синтаксиса
if ! python3 -m py_compile /work/main.py 2>/work/cerr; then
  echo "__COMPILE_ERROR__" >&2
  cat /work/cerr >&2
  exit 2
fi

[ "$MODE" = "compile" ] && exit 0

exec timeout "${TIME_LIMIT:-2}" python3 /work/main.py

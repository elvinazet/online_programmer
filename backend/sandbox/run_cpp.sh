#!/bin/sh
# Entrypoint sandbox для C++. Исходник — в SRC_B64, тест — на stdin.
set -e
echo "$SRC_B64" | base64 -d > /work/main.cpp

if ! g++ -O2 -std=c++17 -o /work/prog /work/main.cpp 2>/work/cerr; then
  echo "__COMPILE_ERROR__" >&2
  cat /work/cerr >&2
  exit 2
fi

[ "$MODE" = "compile" ] && exit 0

exec timeout "${TIME_LIMIT:-2}" /work/prog

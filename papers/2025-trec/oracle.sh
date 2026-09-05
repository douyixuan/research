#!/usr/bin/env bash
set -euo pipefail
ulimit -t 20
rm -f small.out
if ! timeout -s KILL 10 gcc -std=c11 -O0 small.c -o small.out >compile.log 2>&1; then
  exit 1
fi
set +e
timeout -s KILL 5 ./small.out >run.log 2>&1
rc=$?
set -e
rm -f small.out
[[ "$rc" -eq 7 ]]

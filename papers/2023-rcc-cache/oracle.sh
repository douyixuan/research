#!/usr/bin/env bash
set -euo pipefail

# reproduce.sh substitutes an absolute counter path before handing this script
# to Perses, avoiding reliance on environment propagation into test subprocesses.
COUNTER_FILE="__COUNTER_FILE__"
count=0
if [[ -f "$COUNTER_FILE" ]]; then
  count="$(cat "$COUNTER_FILE")"
fi
printf '%s\n' "$((count + 1))" > "$COUNTER_FILE"

gcc -std=c11 -O0 small.c -o small.out >/dev/null 2>&1
set +e
./small.out >/dev/null 2>&1
rc=$?
set -e
[[ "$rc" -eq 12 ]]

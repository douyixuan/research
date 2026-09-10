#!/usr/bin/env bash
set -euo pipefail

: "${COUNTER_FILE:?COUNTER_FILE must be set}"
count=0
if [[ -f "$COUNTER_FILE" ]]; then
  count="$(cat "$COUNTER_FILE")"
fi
printf '%s\n' "$((count + 1))" > "$COUNTER_FILE"

# Keep the twelve identical increments so deletions at different positions can
# create duplicate textual variants while still being rejected by the oracle.
inc_count="$(grep -oF '+=' small.c | wc -l | tr -d ' ')"
[[ "$inc_count" == "12" ]] || exit 1

gcc -std=c11 -O0 small.c -o small.out >/dev/null 2>&1
./small.out

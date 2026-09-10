#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

rm -rf "$RESULTS" "$WORK/nocache" "$WORK/rcc"
mkdir -p "$RESULTS" "$WORK"

# Deterministic mechanism-level trace of compact encoding + refreshing.
python3 "$PAPER_DIR/reproduce.py"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha256="$(sha256sum "$JAR" | awk '{print $1}')"
[[ "$actual_sha256" == "$PERSES_SHA256" ]] || {
  echo "Perses checksum mismatch: $actual_sha256" >&2
  exit 10
}

run_case() {
  local label="$1"; shift
  local dir="$WORK/$label"
  mkdir -p "$dir"
  cp "$PAPER_DIR/case/small.c" "$dir/small.c"
  cp "$PAPER_DIR/oracle.sh" "$dir/oracle.sh"
  chmod +x "$dir/oracle.sh"

  export COUNTER_FILE="$RESULTS/${label}.oracle-count"
  printf '0\n' > "$COUNTER_FILE"

  if ! (
    cd "$dir"
    java -jar "$JAR" \
      "$@" \
      --enable-vulcan false \
      --enable-latra false \
      --enable-sfc false \
      --enable-lpr false \
      --enable-trec false \
      --threads 1 \
      --code-format ORIG_FORMAT \
      --test-script oracle.sh \
      --input-file small.c \
      --output-dir out \
      >"$RESULTS/${label}.log" 2>&1
  ); then
    echo "Perses failed for $label" >&2
    cat "$RESULTS/${label}.log" >&2
    exit 11
  fi

  local reduced
  reduced="$(find "$dir/out" -type f -name 'small.c' -print -quit)"
  [[ -n "$reduced" ]] || {
    echo "No reduced small.c found for $label" >&2
    find "$dir" -maxdepth 3 -type f -print >&2
    exit 12
  }
  cp "$reduced" "$RESULTS/${label}.c"

  # Verify the final file without contaminating the measured oracle counter.
  local verify_counter="$RESULTS/${label}.verify-count"
  (
    export COUNTER_FILE="$verify_counter"
    cd "$RESULTS"
    cp "$PAPER_DIR/oracle.sh" oracle-check.sh
    chmod +x oracle-check.sh
    cp "${label}.c" small.c
    ./oracle-check.sh
    rm -f small.c small.out oracle-check.sh
  )
  rm -f "$verify_counter"
}

# Current-release probe of the paper's official Perses implementation.
run_case nocache --query-caching FALSE
run_case rcc --query-caching TRUE --query-cache-type COMPACT_QUERY_CACHE

NO_CACHE_CALLS="$(cat "$RESULTS/nocache.oracle-count")"
RCC_CALLS="$(cat "$RESULTS/rcc.oracle-count")"
INPUT_BYTES="$(wc -c < "$PAPER_DIR/case/small.c" | tr -d ' ')"
NO_CACHE_BYTES="$(wc -c < "$RESULTS/nocache.c" | tr -d ' ')"
RCC_BYTES="$(wc -c < "$RESULTS/rcc.c" | tr -d ' ')"
SAME_TEXT=false
if cmp -s "$RESULTS/nocache.c" "$RESULTS/rcc.c"; then SAME_TEXT=true; fi

[[ "$RCC_CALLS" -le "$NO_CACHE_CALLS" ]] || {
  echo "Unexpected: RCC issued more external oracle calls than no-cache" >&2
  exit 13
}

NO_CACHE_CALLS="$NO_CACHE_CALLS" RCC_CALLS="$RCC_CALLS" \
INPUT_BYTES="$INPUT_BYTES" NO_CACHE_BYTES="$NO_CACHE_BYTES" RCC_BYTES="$RCC_BYTES" \
SAME_TEXT="$SAME_TEXT" PERSES_SHA256="$PERSES_SHA256" \
python3 - <<'PY' > "$RESULTS/live-perses-summary.json"
import json, os
n = int(os.environ['NO_CACHE_CALLS'])
r = int(os.environ['RCC_CALLS'])
summary = {
    'level': 'scoped L2 current-release Perses probe; not paper-scale L3 and not L1',
    'perses_release': 'v2.7',
    'perses_sha256': os.environ['PERSES_SHA256'],
    'input_bytes': int(os.environ['INPUT_BYTES']),
    'no_cache_oracle_calls': n,
    'rcc_oracle_calls': r,
    'oracle_calls_avoided': n - r,
    'oracle_call_reduction_pct': round(100.0 * (n-r) / n, 2) if n else 0.0,
    'no_cache_reduced_bytes': int(os.environ['NO_CACHE_BYTES']),
    'rcc_reduced_bytes': int(os.environ['RCC_BYTES']),
    'same_reduced_text': os.environ['SAME_TEXT'].lower() == 'true',
    'configuration': {
        'nocache': '--query-caching FALSE',
        'rcc': '--query-caching TRUE --query-cache-type COMPACT_QUERY_CACHE',
        'threads': 1,
        'other_reducers_disabled': ['vulcan', 'latra', 'sfc', 'lpr', 'trec'],
    },
    'oracle': 'requires 12 += occurrences, then gcc -O0 compile and execute',
}
print(json.dumps(summary, indent=2))
PY

cat "$RESULTS/mechanism-summary.json"
cat "$RESULTS/live-perses-summary.json"

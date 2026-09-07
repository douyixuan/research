#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

rm -rf "$RESULTS" "$WORK/cdd" "$WORK/probdd"
mkdir -p "$RESULTS" "$WORK"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha256="$(sha256sum "$JAR" | awk '{print $1}')"
[[ "$actual_sha256" == "$PERSES_SHA256" ]] || {
  echo "Perses release checksum mismatch: $actual_sha256" >&2
  exit 10
}

run_case() {
  local label="$1"
  local minimizer="$2"
  local dir="$WORK/$label"
  mkdir -p "$dir"
  cp "$PAPER_DIR/case/t.c" "$dir/t.c"
  cp "$PAPER_DIR/oracle.sh" "$dir/oracle.sh"
  chmod +x "$dir/oracle.sh"

  (
    cd "$dir"
    java -jar "$JAR" \
      --alg node_priority \
      --default-list-minimizer-for-kleene "$minimizer" \
      --fully-deterministic-mode true \
      --enable-vulcan false \
      --enable-latra false \
      --enable-sfc false \
      --enable-lpr false \
      --enable-trec false \
      --threads 1 \
      --code-format ORIG_FORMAT \
      --test-script oracle.sh \
      --input-file t.c \
      --output-dir out \
      > "$RESULTS/${label}.log" 2>&1
  )

  local reduced
  reduced="$(find "$dir/out" -type f -name 't.c' -print -quit)"
  [[ -n "$reduced" ]] || {
    echo "No reduced t.c found for $label" >&2
    cat "$RESULTS/${label}.log" >&2
    exit 11
  }
  cp "$reduced" "$RESULTS/${label}.c"

  local queries=0
  if [[ -f "$dir/oracle-count.log" ]]; then
    queries="$(wc -l < "$dir/oracle-count.log" | tr -d ' ')"
  fi
  echo "$queries" > "$RESULTS/${label}-queries.txt"

  # Fresh validation of the produced reducer output. This validation is not
  # included in the query count above.
  local validate="$WORK/validate-$label"
  rm -rf "$validate"
  mkdir -p "$validate"
  cp "$RESULTS/${label}.c" "$validate/t.c"
  cp "$PAPER_DIR/oracle.sh" "$validate/oracle.sh"
  chmod +x "$validate/oracle.sh"
  (cd "$validate" && ./oracle.sh)
}

run_case cdd CDD
run_case probdd PROBDD

INPUT_BYTES="$(wc -c < "$PAPER_DIR/case/t.c" | tr -d ' ')"
CDD_BYTES="$(wc -c < "$RESULTS/cdd.c" | tr -d ' ')"
PROBDD_BYTES="$(wc -c < "$RESULTS/probdd.c" | tr -d ' ')"
CDD_QUERIES="$(cat "$RESULTS/cdd-queries.txt")"
PROBDD_QUERIES="$(cat "$RESULTS/probdd-queries.txt")"

INPUT_BYTES="$INPUT_BYTES" CDD_BYTES="$CDD_BYTES" PROBDD_BYTES="$PROBDD_BYTES" \
CDD_QUERIES="$CDD_QUERIES" PROBDD_QUERIES="$PROBDD_QUERIES" \
python3 - <<'PY' > "$RESULTS/summary.json"
import json, os
inp = int(os.environ['INPUT_BYTES'])
cdd = int(os.environ['CDD_BYTES'])
prob = int(os.environ['PROBDD_BYTES'])
cq = int(os.environ['CDD_QUERIES'])
pq = int(os.environ['PROBDD_QUERIES'])
print(json.dumps({
    'level': 'L0 artifact audit + scoped L2 current-Perses live comparison',
    'paper': 'Toward a Better Understanding of Probabilistic Delta Debugging',
    'perses_release': 'v2.7',
    'perses_sha256': '1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427',
    'case_provenance': 'uw-pluverse/perses v2.7 test/org/perses/benchmark_toys/delta_1',
    'oracle': 'upstream-style gcc+clang compile, run, require output containing world',
    'input_bytes': inp,
    'cdd_bytes': cdd,
    'probdd_bytes': prob,
    'cdd_query_count': cq,
    'probdd_query_count': pq,
    'query_delta_cdd_minus_probdd': cq - pq,
    'cdd_vs_probdd_query_change_pct': round((cq - pq) * 100.0 / pq, 4) if pq else None,
    'both_outputs_freshly_validated': True,
    'claim_scope': 'single upstream toy case on current Perses; not author artifact L1 and not paper-scale L3'
}, indent=2))
PY

cat "$RESULTS/summary.json"

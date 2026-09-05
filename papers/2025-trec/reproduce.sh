#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

rm -rf "$RESULTS" "$WORK/baseline" "$WORK/trec"
mkdir -p "$RESULTS" "$WORK"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha256="$(sha256sum "$JAR" | awk '{print $1}')"
echo "Perses v2.7 expected SHA-256: $PERSES_SHA256"
echo "Perses v2.7 actual   SHA-256: $actual_sha256"
if [[ "$actual_sha256" != "$PERSES_SHA256" ]]; then
  echo 'Perses release checksum mismatch' >&2
  exit 10
fi

run_case() {
  local label="$1"
  local trec="$2"
  local dir="$WORK/$label"
  mkdir -p "$dir"
  cp "$PAPER_DIR/case/small.c" "$dir/small.c"
  cp "$PAPER_DIR/oracle.sh" "$dir/oracle.sh"
  chmod +x "$dir/oracle.sh"

  if ! (
    cd "$dir"
    java -jar "$JAR" \
      --alg perses \
      --enable-trec "$trec" \
      --enable-vulcan false \
      --threads 1 \
      --code-format ORIG_FORMAT \
      --test-script oracle.sh \
      --input-file small.c \
      --output-dir out \
      >"$RESULTS/${label}.log" 2>&1
  ); then
    echo "Perses failed for $label; reducer log follows:" >&2
    cat "$RESULTS/${label}.log" >&2
    exit 11
  fi

  local reduced
  reduced="$(find "$dir/out" -type f -name 'small.c' -print -quit)"
  if [[ -z "$reduced" ]]; then
    echo "No reduced small.c found for $label" >&2
    find "$dir" -maxdepth 3 -type f -print >&2
    exit 2
  fi
  cp "$reduced" "$RESULTS/${label}.c"
  (
    cd "$RESULTS"
    cp "$PAPER_DIR/oracle.sh" oracle-check.sh
    chmod +x oracle-check.sh
    cp "${label}.c" small.c
    ./oracle-check.sh
    rm -f small.c oracle-check.sh compile.log run.log
  )
}

run_case baseline false
run_case trec true

baseline_bytes="$(wc -c < "$RESULTS/baseline.c" | tr -d ' ')"
trec_bytes="$(wc -c < "$RESULTS/trec.c" | tr -d ' ')"
input_bytes="$(wc -c < "$PAPER_DIR/case/small.c" | tr -d ' ')"

if grep -q 'ExtremelyLongIdentifierForTRecDemo' "$RESULTS/trec.c"; then
  echo 'T-Rec did not canonicalize the long identifier' >&2
  exit 3
fi
if (( trec_bytes >= baseline_bytes )); then
  echo "Expected T-Rec output to be smaller: trec=$trec_bytes baseline=$baseline_bytes" >&2
  exit 4
fi

INPUT_BYTES="$input_bytes" BASELINE_BYTES="$baseline_bytes" TREC_BYTES="$trec_bytes" \
python3 - <<'PY' > "$RESULTS/l2-summary.json"
import json, os
inp = int(os.environ['INPUT_BYTES'])
base = int(os.environ['BASELINE_BYTES'])
trec = int(os.environ['TREC_BYTES'])
print(json.dumps({
    'level': 'scoped L2 live-minimal',
    'perses_release': 'v2.7',
    'perses_sha256': '1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427',
    'input_bytes': inp,
    'baseline_bytes': base,
    'trec_bytes': trec,
    'trec_vs_baseline_byte_reduction_pct': round((base - trec) * 100.0 / base, 4),
    'oracle': 'gcc -O0 compile + process exit code == 7',
    'baseline_oracle_pass': True,
    'trec_oracle_pass': True,
    'long_identifier_removed_by_trec': True,
    'claim_scope': 'single synthetic C mechanism case; not paper-scale L1/L3'
}, indent=2))
PY

cat "$RESULTS/l2-summary.json"

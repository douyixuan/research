#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

rm -rf "$RESULTS" "$WORK/direct_trec" "$WORK/modern_off" "$WORK/modern_on"
mkdir -p "$RESULTS" "$WORK"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha256="$(sha256sum "$JAR" | awk '{print $1}')"
echo "Perses v2.7 expected SHA-256: $PERSES_SHA256"
echo "Perses v2.7 actual   SHA-256: $actual_sha256"
[[ "$actual_sha256" == "$PERSES_SHA256" ]] || { echo 'Perses release checksum mismatch' >&2; exit 10; }

run_case() {
  local label="$1"; shift
  local dir="$WORK/$label"
  mkdir -p "$dir"
  cp "$PAPER_DIR/case/small.c" "$dir/small.c"
  cp "$PAPER_DIR/oracle.sh" "$dir/oracle.sh"
  chmod +x "$dir/oracle.sh"

  if ! (
    cd "$dir"
    java -jar "$JAR" \
      "$@" \
      --enable-vulcan false \
      --enable-latra false \
      --enable-sfc false \
      --enable-lpr false \
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
  [[ -n "$reduced" ]] || { echo "No reduced small.c found for $label" >&2; find "$dir" -maxdepth 3 -type f -print >&2; exit 2; }
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

# Direct execution of the actual T-Rec reducer registered by v2.7.
run_case direct_trec --alg token_canonicalizer --enable-trec false
# Separate modern-pipeline drift probe. These are NOT paper-era Perses baselines.
run_case modern_off --enable-trec false
run_case modern_on --enable-trec true

input_bytes="$(wc -c < "$PAPER_DIR/case/small.c" | tr -d ' ')"
direct_bytes="$(wc -c < "$RESULTS/direct_trec.c" | tr -d ' ')"
off_bytes="$(wc -c < "$RESULTS/modern_off.c" | tr -d ' ')"
on_bytes="$(wc -c < "$RESULTS/modern_on.c" | tr -d ' ')"

if grep -q 'ExtremelyLongIdentifierForTRecDemo' "$RESULTS/direct_trec.c"; then
  echo 'Direct T-Rec did not canonicalize the long identifier' >&2
  exit 3
fi

INPUT_BYTES="$input_bytes" DIRECT_BYTES="$direct_bytes" OFF_BYTES="$off_bytes" ON_BYTES="$on_bytes" \
DIRECT_LONG="$(grep -q 'ExtremelyLongIdentifierForTRecDemo' "$RESULTS/direct_trec.c" && echo true || echo false)" \
OFF_LONG="$(grep -q 'ExtremelyLongIdentifierForTRecDemo' "$RESULTS/modern_off.c" && echo true || echo false)" \
ON_LONG="$(grep -q 'ExtremelyLongIdentifierForTRecDemo' "$RESULTS/modern_on.c" && echo true || echo false)" \
python3 - <<'PY' > "$RESULTS/l2-summary.json"
import json, os
inp = int(os.environ['INPUT_BYTES'])
direct = int(os.environ['DIRECT_BYTES'])
off = int(os.environ['OFF_BYTES'])
on = int(os.environ['ON_BYTES'])
b = lambda k: os.environ[k].lower() == 'true'
print(json.dumps({
    'level': 'L0 + scoped L2 direct T-Rec mechanism + v2.7 pipeline drift probe',
    'perses_release': 'v2.7',
    'perses_sha256': '1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427',
    'direct_algorithm': 'token_canonicalizer',
    'input_bytes': inp,
    'direct_trec_bytes': direct,
    'direct_trec_byte_change_pct_vs_input': round((inp - direct) * 100.0 / inp, 4),
    'modern_pipeline_trec_off_bytes': off,
    'modern_pipeline_trec_on_bytes': on,
    'modern_pipeline_marginal_byte_delta': off - on,
    'direct_long_identifier_still_present': b('DIRECT_LONG'),
    'modern_off_long_identifier_still_present': b('OFF_LONG'),
    'modern_on_long_identifier_still_present': b('ON_LONG'),
    'oracle': 'gcc -O0 compile + process exit code == 7',
    'all_three_oracle_pass': True,
    'auxiliary_transformers_disabled': ['vulcan', 'latra', 'sfc', 'lpr'],
    'claim_scope': 'single synthetic C mechanism case; not L1 and not paper-scale L3'
}, indent=2))
PY

cat "$RESULTS/l2-summary.json"

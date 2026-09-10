#!/usr/bin/env bash
set -euo pipefail

label="${1:?usage: live_case.sh default|nocache|rcc}"
[[ "$label" == "default" || "$label" == "nocache" || "$label" == "rcc" ]] || { echo "unknown case: $label" >&2; exit 2; }

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
# v2.7 removed the public --query-cache-type selector while leaving the old RCC
# benchmark scripts in-tree. v1.9 is a tagged post-paper release whose published
# CLI usage still exposes COMPACT_QUERY_CACHE, so use it for the live RCC probe.
PERSES_VERSION="v1.9"
PERSES_SIZE="70349824"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses-${PERSES_VERSION}.jar}"

dir="$WORK/$label"
rm -rf "$dir"
mkdir -p "$RESULTS" "$WORK" "$dir"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_size="$(stat -c '%s' "$JAR")"
[[ "$actual_size" == "$PERSES_SIZE" ]] || {
  echo "Perses release size mismatch: expected $PERSES_SIZE got $actual_size" >&2
  exit 10
}

cp "$PAPER_DIR/case/small.c" "$dir/small.c"
counter="$RESULTS/${label}.oracle-count"
printf '0\n' > "$counter"
sed "s|__COUNTER_FILE__|$counter|g" "$PAPER_DIR/oracle.sh" > "$dir/oracle.sh"
chmod +x "$dir/oracle.sh"

cache_flags=()
case "$label" in
  default) cache_flags=() ;;
  nocache) cache_flags=(--query-caching FALSE) ;;
  rcc) cache_flags=(--query-caching TRUE --query-cache-type COMPACT_QUERY_CACHE) ;;
esac

# Keep the invocation deliberately minimal so it matches the v1.9 published CLI
# rather than today's reducer defaults/options.
if ! (
  cd "$dir"
  java -jar "$JAR" \
    "${cache_flags[@]}" \
    --threads 1 \
    --test-script oracle.sh \
    --input-file small.c \
    --output-dir out \
    >"$RESULTS/${label}.log" 2>&1
); then
  echo "Perses failed for $label" >&2
  cat "$RESULTS/${label}.log" >&2
  exit 11
fi

reduced="$(find "$dir/out" -type f -name 'small.c' -print -quit)"
[[ -n "$reduced" ]] || {
  echo "No reduced small.c found for $label" >&2
  find "$dir" -maxdepth 3 -type f -print >&2
  exit 12
}
cp "$reduced" "$RESULTS/${label}.c"

# Verify final property with an isolated counter.
verify_counter="$RESULTS/${label}.verify-count"
sed "s|__COUNTER_FILE__|$verify_counter|g" "$PAPER_DIR/oracle.sh" > "$RESULTS/oracle-check.sh"
chmod +x "$RESULTS/oracle-check.sh"
(
  cd "$RESULTS"
  cp "${label}.c" small.c
  ./oracle-check.sh
  rm -f small.c small.out
)
rm -f "$RESULTS/oracle-check.sh" "$verify_counter"

printf '%s: oracle_calls=%s reduced_bytes=%s\n' \
  "$label" "$(cat "$counter")" "$(wc -c < "$RESULTS/${label}.c" | tr -d ' ')"

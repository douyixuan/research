#!/usr/bin/env bash
set -euo pipefail

label="${1:?usage: live_case.sh nocache|rcc}"
[[ "$label" == "nocache" || "$label" == "rcc" ]] || { echo "unknown case: $label" >&2; exit 2; }

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

dir="$WORK/$label"
rm -rf "$dir"
mkdir -p "$RESULTS" "$WORK" "$dir"

if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha256="$(sha256sum "$JAR" | awk '{print $1}')"
[[ "$actual_sha256" == "$PERSES_SHA256" ]] || {
  echo "Perses checksum mismatch: $actual_sha256" >&2
  exit 10
}

cp "$PAPER_DIR/case/small.c" "$dir/small.c"
counter="$RESULTS/${label}.oracle-count"
printf '0\n' > "$counter"
sed "s|__COUNTER_FILE__|$counter|g" "$PAPER_DIR/oracle.sh" > "$dir/oracle.sh"
chmod +x "$dir/oracle.sh"

case "$label" in
  nocache) cache_flags=(--edit-caching false --query-caching false) ;;
  rcc) cache_flags=(--query-caching true --query-cache-type COMPACT_QUERY_CACHE) ;;
esac

if ! (
  cd "$dir"
  java -jar "$JAR" \
    "${cache_flags[@]}" \
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

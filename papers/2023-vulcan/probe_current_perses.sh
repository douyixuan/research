#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$HERE/results"
WORK="$HERE/.work"
PERSES_VERSION="v2.7"
PERSES_SHA256="1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427"
PERSES_URL="https://github.com/uw-pluverse/perses/releases/download/${PERSES_VERSION}/perses_deploy.jar"
JAR="${PERSES_JAR:-$WORK/perses_deploy.jar}"

mkdir -p "$RESULTS" "$WORK"
if [[ ! -f "$JAR" ]]; then
  curl --fail --location --retry 3 "$PERSES_URL" -o "$JAR"
fi
actual_sha="$(sha256sum "$JAR" | awk '{print $1}')"
[[ "$actual_sha" == "$PERSES_SHA256" ]] || { echo "Perses checksum mismatch" >&2; exit 10; }

run_one() {
  local label="$1"; shift
  local dir="$WORK/$label"
  rm -rf "$dir"
  mkdir -p "$dir"
  cp "$HERE/case/small.c" "$dir/small.c"
  cp "$HERE/oracle.sh" "$dir/oracle.sh"
  chmod +x "$dir/oracle.sh"
  (
    cd "$dir"
    java -jar "$JAR" \
      --threads 1 \
      --code-format ORIG_FORMAT \
      --test-script oracle.sh \
      --input-file small.c \
      --output-dir out \
      --enable-latra false \
      --enable-sfc false \
      --enable-lpr false \
      --enable-trec false \
      "$@" \
      >"$RESULTS/${label}.log" 2>&1
  )
  reduced="$(find "$dir/out" -type f -name small.c -print -quit)"
  [[ -n "$reduced" ]] || { echo "No reduced file for $label" >&2; cat "$RESULTS/${label}.log" >&2; exit 11; }
  cp "$reduced" "$RESULTS/${label}.c"
  (
    cd "$RESULTS"
    cp "$HERE/oracle.sh" oracle-check.sh
    chmod +x oracle-check.sh
    cp "${label}.c" small.c
    ./oracle-check.sh
    rm -f small.c small.out oracle-check.sh
  )
}

run_one current_perses_vulcan_off --enable-vulcan false
run_one current_perses_vulcan_on --enable-vulcan true --vulcan-fixpoint true

python3 - "$RESULTS/current_perses_vulcan_off.c" "$RESULTS/current_perses_vulcan_on.c" <<'PY' > "$RESULTS/current-perses-summary.json"
import json, pathlib, re, sys
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||[-+*/%=;(),{}]")
off = pathlib.Path(sys.argv[1]).read_text()
on = pathlib.Path(sys.argv[2]).read_text()
def m(s): return {"bytes": len(s.encode()), "tokens_proxy": len(TOKEN_RE.findall(s)), "source": s}
mo, mn = m(off), m(on)
print(json.dumps({
  "level": "L0 implementation-drift probe; current Perses v2.7, not paper-era artifact",
  "perses_version": "v2.7",
  "perses_sha256": "1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427",
  "vulcan_off": mo,
  "vulcan_on": mn,
  "byte_delta_off_minus_on": mo["bytes"] - mn["bytes"],
  "token_proxy_delta_off_minus_on": mo["tokens_proxy"] - mn["tokens_proxy"]
}, indent=2))
PY
cat "$RESULTS/current-perses-summary.json"

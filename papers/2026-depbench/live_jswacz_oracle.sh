#!/usr/bin/env bash
set -euo pipefail

BASE_SHA=167febc84b6183c4c971e5aec743e79406a4f847
MANIFEST_SHA=857cbdec952f14b9116c093b89aa62034ae6aa23
REPAIR_SHA=12fe776401cfc219a32d49573d1505acc4063708
UPSTREAM=https://github.com/harvard-lil/js-wacz.git
PAPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$PAPER_DIR/results/js-wacz"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$RESULTS"

printf 'upstream=%s\nbase=%s\nmanifest=%s\nrepair=%s\nnode=%s\nnpm=%s\n' \
  "$UPSTREAM" "$BASE_SHA" "$MANIFEST_SHA" "$REPAIR_SHA" "$(node --version)" "$(npm --version)" \
  > "$RESULTS/environment.txt"

git clone --quiet "$UPSTREAM" "$WORK/js-wacz"
cd "$WORK/js-wacz"

git cat-file -e "$BASE_SHA^{commit}"
git cat-file -e "$MANIFEST_SHA^{commit}"
git cat-file -e "$REPAIR_SHA^{commit}"

reset_base() {
  git reset --hard "$BASE_SHA" >/dev/null
  git clean -fdx >/dev/null
}
apply_manifest() {
  git show "$MANIFEST_SHA" -- package.json package-lock.json | git apply
}
apply_repair() {
  git show "$REPAIR_SHA" -- index.js | git apply
}
apply_test() {
  git show "$REPAIR_SHA" -- index.test.js | git apply
}

run_oracle() {
  local name="$1" expected="$2"
  shift 2
  reset_base
  for op in "$@"; do "$op"; done
  local log="$RESULTS/${name}.log"
  set +e
  {
    echo "== npm ci =="
    npm ci
    echo "== npm test =="
    npm test
  } >"$log" 2>&1
  local rc=$?
  set -e
  local actual=pass
  if [[ $rc -ne 0 ]]; then actual=fail; fi
  printf '%s\texpected=%s\tactual=%s\trc=%s\n' "$name" "$expected" "$actual" "$rc" | tee -a "$RESULTS/oracle.tsv"
  [[ "$actual" == "$expected" ]]
}

: > "$RESULTS/oracle.tsv"
run_oracle base pass
run_oracle manifest_plus_test fail apply_manifest apply_test
run_oracle manifest_plus_repair_plus_test pass apply_manifest apply_repair apply_test
run_oracle repair_plus_test_no_manifest fail apply_repair apply_test

python3 - "$RESULTS/oracle.tsv" "$RESULTS/oracle.json" <<'PY'
import json, sys
src, dst = sys.argv[1:]
rows = []
for line in open(src):
    name, expected, actual, rc = line.rstrip().split('\t')
    rows.append({
        "state": name,
        "expected": expected.split('=',1)[1],
        "actual": actual.split('=',1)[1],
        "return_code": int(rc.split('=',1)[1]),
    })
json.dump({
    "reproduction_level": "scoped L2 case reconstruction, not official DepBench release task",
    "paper_example": "harvard-lil/js-wacz#41 glob 8.1.0 -> 10.3.3",
    "four_state_oracle_satisfied": all(r["expected"] == r["actual"] for r in rows),
    "states": rows,
}, open(dst, 'w'), indent=2)
open(dst, 'a').write('\n')
PY

cat "$RESULTS/oracle.json"

#!/usr/bin/env bash
set -euo pipefail

repo="$(mktemp -d)"
cleanup() { rm -rf "$repo"; }
trap cleanup EXIT
cd "$repo"

git init -q
git config user.email ci@example.invalid
git config user.name ci

cat > compiler.py <<'PY'
def compile_case(case):
    return {"a": 10, "b": 20, "c": 30}[case]
PY
git add compiler.py
git commit -qm 'good baseline'
GOOD=$(git rev-parse HEAD)

printf '\n# harmless refactor\n' >> compiler.py
git add compiler.py
git commit -qm 'harmless refactor'

cat > compiler.py <<'PY'
def compile_case(case):
    # One regression manifests through two syntactically distinct tests.
    if case in {"a", "b"}:
        return {"a": 11, "b": 21}[case]
    return 30
PY
git add compiler.py
git commit -qm 'introduce fold bug'
BUG_AB=$(git rev-parse HEAD)

cat > compiler.py <<'PY'
def compile_case(case):
    # The first regression survives; a second independent regression appears.
    if case in {"a", "b"}:
        return {"a": 11, "b": 21}[case]
    if case == "c":
        return 31
    raise KeyError(case)
PY
git add compiler.py
git commit -qm 'introduce vector bug'
BUG_C=$(git rev-parse HEAD)
BAD=$(git rev-parse HEAD)

cat > checker.py <<'PY'
import importlib.util
import sys

case = sys.argv[1]
expected = {"a": 10, "b": 20, "c": 30}[case]
spec = importlib.util.spec_from_file_location("compiler", "compiler.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.exit(0 if mod.compile_case(case) == expected else 1)
PY

bisect_case() {
  local case="$1"
  local log="bisect-${case}.log"
  git bisect start "$BAD" "$GOOD" >/dev/null 2>&1
  # git-bisect run returns the tested command's status semantics, so capture the
  # first-bad line rather than assuming HEAD remains at the first-bad commit.
  git bisect run python checker.py "$case" >"$log" 2>&1 || true
  local found
  found=$(grep -Eo '^[0-9a-f]{40} is the first bad commit' "$log" | tail -1 | cut -d' ' -f1)
  git bisect reset >/dev/null 2>&1
  [[ -n "$found" ]]
  printf '%s\n' "$found"
}

A=$(bisect_case a)
B=$(bisect_case b)
C=$(bisect_case c)

[[ "$A" == "$BUG_AB" ]]
[[ "$B" == "$BUG_AB" ]]
[[ "$C" == "$BUG_C" ]]
[[ "$A" == "$B" ]]
[[ "$A" != "$C" ]]

printf 'case_a_first_bad=%s\n' "$A"
printf 'case_b_first_bad=%s\n' "$B"
printf 'case_c_first_bad=%s\n' "$C"
printf 'dedup_clusters=2\n'
printf 'status=PASS\n'

#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/results"
ARTIFACT_COMMIT="db94d68400e25197c5a93e5f420cf35ec4ae698c"
WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

mkdir -p "$OUT"
rm -f "$OUT"/table2.txt "$OUT"/rq4.txt "$OUT"/artifact-audit.json "$OUT"/live-bisect-smoke.txt

python -m pip install -q -r "$HERE/requirements.txt"

git clone --quiet https://github.com/buglens-artifact/BugLens.git "$WORK/BugLens"
git -C "$WORK/BugLens" checkout --quiet "$ARTIFACT_COMMIT"

python "$HERE/audit_artifact.py" "$WORK/BugLens" --out "$OUT/artifact-audit.json"

(
  cd "$WORK/BugLens"
  python evaluate.py
) | tee "$OUT/table2.txt"

(
  cd "$WORK/BugLens"
  python rq4.py
) | tee "$OUT/rq4.txt"

bash "$HERE/live_bisect_smoke.sh" | tee "$OUT/live-bisect-smoke.txt"

# Deterministic sanity checks on the released four-dataset evidence.
for dataset in gcc430 gcc440 gcc450 llvm280; do
  grep -q "Dataset: $dataset" "$OUT/table2.txt"
done
grep -q 'status=PASS' "$OUT/live-bisect-smoke.txt"

printf '\nReproduction completed. Evidence: %s\n' "$OUT"

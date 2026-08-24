#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
WORK="${RUNNER_TEMP:-/tmp}/ddmt-reproduction"
UPSTREAM="$WORK/upstream"
PIN="43c2f12306f02582779b24766dbddeadce9480e3"

rm -rf "$WORK"
mkdir -p "$WORK" "$RESULTS"

echo "==> Fetch official DDMT artifact at pinned snapshot $PIN"
git clone --filter=blob:none --no-checkout https://github.com/ymxl85/DDMT.git "$UPSTREAM"
git -C "$UPSTREAM" checkout --detach "$PIN"
ACTUAL="$(git -C "$UPSTREAM" rev-parse HEAD)"
test "$ACTUAL" = "$PIN"

printf '%s\n' "$ACTUAL" > "$RESULTS/upstream-commit.txt"

echo "==> L1: reprocess released Siemens summaries"
python3 "$HERE/recompute_siemens.py" \
  "$UPSTREAM/benchmarks/Siemens" \
  --output "$RESULTS/l1-siemens.json"

echo "==> L2: fresh oracle-less MR-guided ddmin mechanism run"
python3 "$HERE/mechanism_smoke.py" \
  --output "$RESULTS/l2-mechanism.json"

echo "==> Artifact audit"
python3 - "$UPSTREAM" "$RESULTS/artifact-audit.json" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
siemens = root / "benchmarks" / "Siemens"
checks = {
    "ddmin_ddmt_source_exists": (root / "ddmin-DDMT" / "printtokens" / "DDMT.py").exists(),
    "perses_ddmt_exists": (root / "Perses-DDMT").is_dir(),
    "replace_mr1_summary_exists": (siemens / "result-summary--replace-MR1.txt").exists(),
    "replace_mr2_summary_exists": (siemens / "result-summary--replace-MR2.txt").exists(),
    "replace_mr3_summary_exists": (siemens / "result-summary--replace-MR3.txt").exists(),
    "replace_dd_summary_exists": (siemens / "result-summary--replace-dd.txt").exists(),
}
report = {
    "upstream_commit": "43c2f12306f02582779b24766dbddeadce9480e3",
    "checks": checks,
    "reproducibility_gap": (
        "Paper Table V names replace/MR3 as the best MR, but its summary file is absent from this snapshot."
        if not checks["replace_mr3_summary_exists"] else None
    ),
}
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
PY

echo "==> Reproduction complete"
ls -l "$RESULTS"

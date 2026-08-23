#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$HERE/results"
PIN="c3180d6f3daa083a4138b8593246b10b99414072"
ARTIFACT_DIR="${RUNNER_TEMP:-/tmp}/drreduce-data-$PIN"

rm -rf "$RESULTS" "$ARTIFACT_DIR"
mkdir -p "$RESULTS" "$ARTIFACT_DIR"

git -C "$ARTIFACT_DIR" init -q
git -C "$ARTIFACT_DIR" remote add origin https://github.com/XYZboom/DRReduceData.git
git -C "$ARTIFACT_DIR" fetch -q --depth 1 origin "$PIN"
git -C "$ARTIFACT_DIR" checkout -q --detach FETCH_HEAD

ACTUAL="$(git -C "$ARTIFACT_DIR" rev-parse HEAD)"
if [[ "$ACTUAL" != "$PIN" ]]; then
  echo "artifact pin mismatch: expected $PIN, got $ACTUAL" >&2
  exit 1
fi

python3 "$HERE/artifact_audit.py" "$ARTIFACT_DIR" --out "$RESULTS/artifact-audit.json"
python3 "$HERE/mini_drreduce.py"

python3 - "$RESULTS" "$PIN" <<'PY'
import json
import sys
from pathlib import Path

results = Path(sys.argv[1])
pin = sys.argv[2]
audit = json.loads((results / "artifact-audit.json").read_text())
mechanism = json.loads((results / "mechanism.json").read_text())
summary = {
    "paper": "DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction",
    "artifact_commit": pin,
    "achieved_level": "scoped L1 + scoped L2 mechanism reproduction",
    "artifact_audit": audit,
    "mechanism": mechanism,
    "l3_blocker": "The public DRReduceData repository exposes evaluation data/results but not the DRReduce reducer implementation or its CLion/PSI integration.",
}
(results / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

rm -rf results
mkdir -p results

python3 mini_scitix.py --output results/mechanism.json
python3 claim_audit.py

if [[ "${SKIP_NETWORK:-0}" != "1" ]]; then
  python3 probe_artifact.py
else
  printf '%s\n' '{"skipped": true, "reason": "SKIP_NETWORK=1"}' > results/artifact_probe.json
fi

python3 - <<'PY'
import json
from pathlib import Path

mechanism = json.loads(Path("results/mechanism.json").read_text())
claims = json.loads(Path("results/claim_drift.json").read_text())
probe = json.loads(Path("results/artifact_probe.json").read_text())
summary = {
    "level": mechanism["reproduction_level"],
    "mechanism_final_candidate": mechanism["motivating_property"]["scitix_like_result"]["final_candidates"],
    "claim_delta_pp": claims["delta_percentage_points_issta_minus_thesis"],
    "artifact_probe": probe,
}
Path("results/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print("\n=== summary ===")
print(json.dumps(summary, indent=2))
PY

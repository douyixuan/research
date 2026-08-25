#!/usr/bin/env bash
set -euo pipefail

PIN="fc83e86f3642e100b9521fe710108facf83e64f7"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

rm -rf "$RESULTS"
mkdir -p "$RESULTS"

git clone --quiet https://github.com/t3-research/lpr-plus.git "$WORK/lpr-plus"
cd "$WORK/lpr-plus"
git checkout --quiet "$PIN"

printf '%s\n' "[1/4] upstream offline tests"
env PYTHONPATH=src python3 -m unittest discover -s tests | tee "$RESULTS/upstream-tests.log"

printf '%s\n' "[2/4] transformation-catalog audit"
env PYTHONPATH=src python3 - <<'PY' | tee "$RESULTS/catalog.json"
import json
from lpr_plus.catalog import load_base_transformations, load_refined_transformations, load_transformations
base = load_base_transformations()
refined = load_refined_transformations()
all_rules = load_transformations("all35")
assert len(base) == 5, len(base)
assert len(refined) == 30, len(refined)
assert len(all_rules) == 35, len(all_rules)
assert len({r.get("id") or r.get("name") for r in all_rules}) == 35
print(json.dumps({"base": len(base), "refined": len(refined), "all": len(all_rules)}, indent=2))
PY

printf '%s\n' "[3/4] oracle-validated mock-provider reduction"
mkdir -p "$WORK/mock"
printf '```c\nint main(void) { return 0; }\n```\n' > "$WORK/mock/response.md"

env PYTHONPATH=src python3 -m lpr_plus reduce \
  --provider mock \
  --mock-response-file "$WORK/mock/response.md" \
  --token-counter simple \
  --lpr-root /tmp/LPR \
  --language c \
  --source examples/small.c \
  --oracle examples/r.sh \
  --transformations all35 \
  --out "$RESULTS/mock-reduce"

printf '%s\n' "[4/4] validate fresh result"
python3 - "$PIN" "$RESULTS/mock-reduce/report.json" "$RESULTS/summary.json" <<'PY'
import json
import pathlib
import sys

pin, report_path, summary_path = sys.argv[1:]
report = json.loads(pathlib.Path(report_path).read_text())
assert report["valid"] is True, report
assert report["initialOracle"]["passed"] is True
assert report["finalOracle"]["passed"] is True
assert report["finalTokens"] < report["initialTokens"], report
assert report["acceptedCount"] >= 1, report
assert report["attemptCount"] == 35, report["attemptCount"]
assert report["apiFailureCount"] == 0, report["apiFailureCount"]

summary = {
    "level": "L0 + scoped L2 live-minimal",
    "upstream": "t3-research/lpr-plus",
    "upstreamCommit": pin,
    "catalog": {"base": 5, "refined": 30, "all": 35},
    "initialTokens": report["initialTokens"],
    "finalTokens": report["finalTokens"],
    "reductionTokens": report["reductionTokens"],
    "reductionPercent": report["reductionPercent"],
    "acceptedCount": report["acceptedCount"],
    "attemptCount": report["attemptCount"],
    "initialOraclePassed": report["initialOracle"]["passed"],
    "finalOraclePassed": report["finalOracle"]["passed"],
    "paperClaim": {
        "pairedCaseMeanLPRTokens": 189.7,
        "pairedCaseMeanLPRPlusTokens": 180.9,
        "meanTokenDelta": 8.8,
        "relativeMeanReductionPercent": 4.6389,
        "recomputedHere": False,
        "blocker": "Official source package does not bundle raw benchmark outputs/API execution evidence."
    }
}
pathlib.Path(summary_path).write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

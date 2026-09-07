#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work/l1"
ZIP="$PAPER_DIR/.work/cdd-artifact.zip"
URL="https://zenodo.org/records/14854239/files/cdd-artifact.zip?download=1"
MD5="21f9b3b3ef43fb2361071de32b09a2c9"

mkdir -p "$RESULTS" "$PAPER_DIR/.work"
rm -rf "$WORK"
mkdir -p "$WORK"

if [[ ! -f "$ZIP" ]]; then
  curl --fail --location --retry 3 "$URL" -o "$ZIP"
fi
actual_md5="$(md5sum "$ZIP" | awk '{print $1}')"
[[ "$actual_md5" == "$MD5" ]] || {
  echo "Artifact MD5 mismatch: $actual_md5" >&2
  exit 20
}

mapfile -t wanted < <(unzip -Z1 "$ZIP" | grep -E '/scripts?/(data\.csv|wilconxon_all\.py|wilconxon_randomness\.py)$' || true)
if [[ ${#wanted[@]} -lt 3 ]]; then
  echo "Could not locate the released p-value data/scripts in the artifact" >&2
  unzip -Z1 "$ZIP" | grep -E 'wilconxon|data\.csv' | head -50 >&2 || true
  exit 21
fi

for entry in "${wanted[@]}"; do
  unzip -q "$ZIP" "$entry" -d "$WORK"
done

all_script="$(find "$WORK" -name wilconxon_all.py -print -quit)"
random_script="$(find "$WORK" -name wilconxon_randomness.py -print -quit)"
data_file="$(find "$WORK" -name data.csv -print -quit)"
[[ -n "$all_script" && -n "$random_script" && -n "$data_file" ]]

scripts_dir="$(dirname "$all_script")"
(
  cd "$scripts_dir"
  python3 ./wilconxon_all.py
) | tee "$RESULTS/l1-wilcoxon-all.txt"
(
  cd "$scripts_dir"
  python3 ./wilconxon_randomness.py
) | tee "$RESULTS/l1-wilcoxon-randomness.txt"
cp "$data_file" "$RESULTS/l1-data.csv"

python3 - <<PY > "$RESULTS/l1-summary.json"
import json
print(json.dumps({
  "level": "L1 partial",
  "artifact": "Zenodo 14854239 v3",
  "artifact_md5": "$MD5",
  "evidence": ["released scripts/data.csv", "released wilconxon_all.py", "released wilconxon_randomness.py"],
  "scope": "reprocesses the authors' precomputed statistical data; does not rerun the 76 benchmark reductions",
  "paper_scale_live_run": False
}, indent=2))
PY

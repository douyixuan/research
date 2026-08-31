#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for tool in python3 yosys iverilog vvp; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 2; }
done
rm -rf results
mkdir -p results
python3 scripts/run_experiment.py

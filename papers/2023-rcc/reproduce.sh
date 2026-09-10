#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf results
mkdir -p results
python3 reproduce.py 2>&1 | tee results/reproduce.log
cat results/summary.md

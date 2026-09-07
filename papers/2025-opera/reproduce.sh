#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf results
mkdir -p results
python3 reproduce.py | tee results/l1.log
python3 mini_tcp.py | tee results/l2-mini.log
printf '\nOPERA reproduction completed.\n'

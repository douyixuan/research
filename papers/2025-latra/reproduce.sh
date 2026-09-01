#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf results
mkdir -p results
python3 reproduce.py

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
rm -rf papers/2025-wdd/results
python3 papers/2025-wdd/reproduce.py

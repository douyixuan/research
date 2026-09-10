#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$PAPER_DIR/results" "$PAPER_DIR/.work/nocache" "$PAPER_DIR/.work/rcc"
mkdir -p "$PAPER_DIR/results" "$PAPER_DIR/.work"

python3 "$PAPER_DIR/reproduce.py"
bash "$PAPER_DIR/live_case.sh" nocache
bash "$PAPER_DIR/live_case.sh" rcc
python3 "$PAPER_DIR/summarize_live.py"

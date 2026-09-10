#!/usr/bin/env bash
set -euo pipefail

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$PAPER_DIR/results" "$PAPER_DIR/.work/default" "$PAPER_DIR/.work/nocache" "$PAPER_DIR/.work/rcc"
mkdir -p "$PAPER_DIR/results" "$PAPER_DIR/.work"

# Always-run deterministic scoped L2 mechanism reproduction.
python3 "$PAPER_DIR/reproduce.py"

# Historical Perses integration is intentionally opt-in because current Perses
# removed the paper's public RCC selector and the v1.9 prebuilt JAR does not run
# successfully in the hosted CI environment used here.
if [[ "${RCC_HISTORICAL_LIVE:-0}" == "1" ]]; then
  bash "$PAPER_DIR/live_case.sh" default
  bash "$PAPER_DIR/live_case.sh" nocache
  bash "$PAPER_DIR/live_case.sh" rcc
  python3 "$PAPER_DIR/summarize_live.py"
fi

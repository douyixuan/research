#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$HERE/results"
mkdir -p "$HERE/results"
python3 "$HERE/reproduce.py"
"$HERE/probe_current_perses.sh"

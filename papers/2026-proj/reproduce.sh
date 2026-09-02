#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
{
  echo '# PROJ reproduction report'
  echo
  echo '## Reported-claim audit (L0 / consistency only)'
  echo '```text'
  python3 check_reported_claims.py
  echo '```'
  echo
  echo '## Legacy architecture smoke'
  echo '```text'
  python3 mini_proj.py
  echo '```'
  echo
  echo '## Independent scoped L2 mechanism'
  echo '```text'
  python3 pipeline_l2.py
  echo '```'
  echo
  echo 'Detailed scoped-L2 event trace: `results/pipeline_l2.json`.'
} | tee results/report.md

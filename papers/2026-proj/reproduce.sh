#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
{
  echo '# PROJ deterministic reproduction report'
  echo
  echo '## Reported-claim audit'
  echo '```text'
  python3 check_reported_claims.py
  echo '```'
  echo
  echo '## Independent harness smoke test'
  echo '```text'
  python3 mini_proj.py
  echo '```'
} | tee results/report.md

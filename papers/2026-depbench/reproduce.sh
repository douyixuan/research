#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-all}"
case "$MODE" in
  claims)
    python3 "$HERE/audit_claims.py"
    ;;
  live)
    bash "$HERE/live_jswacz_oracle.sh"
    ;;
  all)
    python3 "$HERE/audit_claims.py"
    bash "$HERE/live_jswacz_oracle.sh"
    ;;
  *)
    echo "usage: $0 [claims|live|all]" >&2
    exit 2
    ;;
esac

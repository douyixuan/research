#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "${ROOT}/recompute_claims.py"

if [[ "${RUN_OFFICIAL:-1}" == "1" ]]; then
  bash "${ROOT}/probe_official_adhoc.sh"
fi

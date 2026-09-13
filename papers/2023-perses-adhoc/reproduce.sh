#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "${ROOT}/results"
mkdir -p "${ROOT}/results"
python3 "${ROOT}/reproduce.py" | tee "${ROOT}/results/l1.log"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${ROOT}/work"
UPSTREAM="${WORK}/thalia-type"
PIN="08895f35945ac84e78b91db9f908f401246e3c15"

rm -rf "${WORK}"
mkdir -p "${WORK}" "${ROOT}/results"

git clone --filter=blob:none https://github.com/uw-pluverse/thalia-type.git "${UPSTREAM}"
git -C "${UPSTREAM}" checkout --detach "${PIN}"

python -m pip install --disable-pip-version-check --quiet "scipy==1.14.0"

export THALIATYPE_REPORT="${ROOT}/results/thaliatype-report.json"
python "${ROOT}/reproduce.py" "${UPSTREAM}" | tee "${ROOT}/results/reproduction.log"

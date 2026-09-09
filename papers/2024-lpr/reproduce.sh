#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM_COMMIT="d45ea0e261a8f4c7ec05fc29ccb5aadd19d673cc"
WORK_DIR="${LPR_WORK_DIR:-${HERE}/.work}"
UPSTREAM="${WORK_DIR}/LPR"
RESULTS="${HERE}/results"

mkdir -p "${WORK_DIR}" "${RESULTS}"
if [[ ! -d "${UPSTREAM}/.git" ]]; then
  git clone --filter=blob:none https://github.com/zhangxiaosa/LPR.git "${UPSTREAM}"
fi

git -C "${UPSTREAM}" fetch --quiet origin "${UPSTREAM_COMMIT}"
git -C "${UPSTREAM}" checkout --quiet --detach "${UPSTREAM_COMMIT}"

python3 "${HERE}/scripts/recompute.py" \
  --artifact "${UPSTREAM}" \
  --output "${RESULTS}"

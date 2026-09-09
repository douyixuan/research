#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPSTREAM_COMMIT="1cd376048ae5c653fe61745a3d25c4a8a871d361"
WORK_DIR="${LPR_WORK_DIR:-${HERE}/.work}"
UPSTREAM="${WORK_DIR}/LPR"
RESULTS="${HERE}/results"

mkdir -p "${WORK_DIR}" "${RESULTS}"
if [[ ! -d "${UPSTREAM}/.git" ]]; then
  git clone --filter=blob:none --no-checkout https://github.com/zhangxiaosa/LPR.git "${UPSTREAM}"
  git -C "${UPSTREAM}" sparse-checkout init --cone
  git -C "${UPSTREAM}" sparse-checkout set \
    tools \
    benchmark_suites/c/vulcan benchmark_suites/c/lpr_0 benchmark_suites/c/lpr_1 benchmark_suites/c/lpr_2 benchmark_suites/c/lpr_3 benchmark_suites/c/lpr_4 \
    benchmark_suites/rust/vulcan_results benchmark_suites/rust/lpr_0 benchmark_suites/rust/lpr_1 benchmark_suites/rust/lpr_2 benchmark_suites/rust/lpr_3 benchmark_suites/rust/lpr_4 \
    benchmark_suites/js/vulcan_results benchmark_suites/js/lpr_0 benchmark_suites/js/lpr_1 benchmark_suites/js/lpr_2 benchmark_suites/js/lpr_3 benchmark_suites/js/lpr_4
fi

git -C "${UPSTREAM}" checkout --quiet --detach "${UPSTREAM_COMMIT}"

python3 "${HERE}/scripts/recompute.py" \
  --artifact "${UPSTREAM}" \
  --output "${RESULTS}"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${ROOT_DIR}/.work"
OUT_DIR="${ROOT_DIR}/results"
ARTIFACT_REPO="https://github.com/uw-pluverse/lpo-artifact.git"

mkdir -p "${WORK_DIR}" "${OUT_DIR}"

if [[ ! -d "${WORK_DIR}/lpo-artifact/.git" ]]; then
  git clone --depth 1 "${ARTIFACT_REPO}" "${WORK_DIR}/lpo-artifact"
else
  git -C "${WORK_DIR}/lpo-artifact" fetch --depth 1 origin main
  git -C "${WORK_DIR}/lpo-artifact" reset --hard origin/main
fi

ARTIFACT_SHA="$(git -C "${WORK_DIR}/lpo-artifact" rev-parse HEAD)"
printf '%s\n' "${ARTIFACT_SHA}" > "${OUT_DIR}/artifact-commit.txt"

(
  cd "${WORK_DIR}/lpo-artifact"
  python3 parse_rq1_results.py
) | tee "${OUT_DIR}/rq1-summary.txt"

echo "LPO artifact commit: ${ARTIFACT_SHA}"
echo "Results: ${OUT_DIR}/rq1-summary.txt"

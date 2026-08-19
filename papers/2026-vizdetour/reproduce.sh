#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
WORK_DIR="${RESULTS_DIR}/work"
ARTIFACT_DIR="${WORK_DIR}/vizdetour-artifact"
ARTIFACT_SHA="d2b22e33b94eaff06b2116f31ddeea21bb0e6b91"
MATPLOTLIB_VERSION="${MATPLOTLIB_VERSION:-3.10.8}"
VENV_DIR="${REPO_ROOT}/.venv-vizdetour-${MATPLOTLIB_VERSION}"

mkdir -p "${RESULTS_DIR}" "${WORK_DIR}"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  python3 -m venv "${VENV_DIR}"
fi
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install \
  "matplotlib==${MATPLOTLIB_VERSION}" numpy pillow

rm -rf "${ARTIFACT_DIR}"
git clone --quiet https://github.com/smith2936/vizdetour.git "${ARTIFACT_DIR}"
git -C "${ARTIFACT_DIR}" checkout --quiet "${ARTIFACT_SHA}"

"${VENV_DIR}/bin/python" "${SCRIPT_DIR}/audit_artifact.py" \
  "${ARTIFACT_DIR}/dataviz-bugs-detected.csv" \
  --out "${RESULTS_DIR}/artifact-audit.json"

LIVE_OUT="${RESULTS_DIR}/matplotlib-${MATPLOTLIB_VERSION}"
EXPECT=()
if [[ "${MATPLOTLIB_VERSION}" == "3.10.8" ]]; then
  EXPECT+=(--expect-detected)
fi
"${VENV_DIR}/bin/python" "${SCRIPT_DIR}/reproduce.py" \
  --out "${LIVE_OUT}" "${EXPECT[@]}"

echo "VIZDETOUR reproduction complete: ${RESULTS_DIR}"

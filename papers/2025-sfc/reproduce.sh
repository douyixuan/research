#!/usr/bin/env bash
set -euo pipefail

readonly EXPECTED_SHA="6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly RESULTS_DIR="${SCRIPT_DIR}/results"
readonly UPSTREAM_DIR="${1:-${SCRIPT_DIR}/upstream}"
readonly UPSTREAM_REPO="https://github.com/uw-pluverse/perses.git"

mkdir -p "${RESULTS_DIR}"

if [[ ! -d "${UPSTREAM_DIR}/.git" ]]; then
  rm -rf "${UPSTREAM_DIR}"
  git clone "${UPSTREAM_REPO}" "${UPSTREAM_DIR}"
  git -C "${UPSTREAM_DIR}" checkout --detach "${EXPECTED_SHA}"
fi

actual_sha="$(git -C "${UPSTREAM_DIR}" rev-parse HEAD)"
if [[ "${actual_sha}" != "${EXPECTED_SHA}" ]]; then
  echo "ERROR: expected Perses ${EXPECTED_SHA}, got ${actual_sha}" >&2
  exit 2
fi

if command -v bazelisk >/dev/null 2>&1; then
  bazel_cmd="bazelisk"
elif command -v bazel >/dev/null 2>&1; then
  bazel_cmd="bazel"
else
  echo "ERROR: bazelisk or bazel is required" >&2
  exit 2
fi

targets=(
  "//sfc/test/org/perses/reduction/reducer/sfc:PaperExampleSimplificationsTest"
  "//sfc/test/org/perses/reduction/reducer/sfc:SmallerStructureReplacementReducerTest"
  "//sfc/test/org/perses/reduction/reducer/sfc:IdentifierUseEliminationReducerTest"
  "//sfc/test/org/perses/reduction/reducer/sfc:StructureCanonicalizationReducerTest"
)

printf 'upstream_sha=%s\n' "${actual_sha}" | tee "${RESULTS_DIR}/metadata.txt"
printf 'bazel=%s\n' "$(${bazel_cmd} --version 2>/dev/null || true)" | tee -a "${RESULTS_DIR}/metadata.txt"

pushd "${UPSTREAM_DIR}" >/dev/null
passed=0
for target in "${targets[@]}"; do
  safe_name="$(echo "${target##*:}" | tr -cd '[:alnum:]_-')"
  log="${RESULTS_DIR}/${safe_name}.log"
  echo "==> ${target}" | tee "${log}"
  if "${bazel_cmd}" test --test_output=errors "${target}" 2>&1 | tee -a "${log}"; then
    passed=$((passed + 1))
  else
    echo "FAILED: ${target}" >&2
    exit 1
  fi
done
popd >/dev/null

python3 - "${RESULTS_DIR}/summary.json" "${actual_sha}" "${passed}" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
sha = sys.argv[2]
passed = int(sys.argv[3])
summary = {
    "paper": "Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations",
    "level": "scoped L2 mechanism reproduction",
    "upstream_commit": sha,
    "official_targets_run": 4,
    "official_targets_passed": passed,
    "paper_example_count_claimed_by_upstream_test": 12,
    "paper_scale_benchmark_reproduced": False,
}
out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(out.read_text(), end="")
PY

#!/usr/bin/env bash
set -euo pipefail

readonly PERSES_COMMIT="${PERSES_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly RESULTS_DIR="${ROOT_DIR}/results"
readonly WORK_DIR="${RUNNER_TEMP:-/tmp}/perses-sfc-${PERSES_COMMIT:0:12}"

mkdir -p "${RESULTS_DIR}"
rm -f "${RESULTS_DIR}/bazel-tests.log" "${RESULTS_DIR}/summary.txt"
rm -rf "${WORK_DIR}"

if command -v bazelisk >/dev/null 2>&1; then
  BAZEL=bazelisk
elif command -v bazel >/dev/null 2>&1; then
  BAZEL=bazel
else
  echo "error: Bazel/Bazelisk is required" >&2
  exit 2
fi

echo "Fetching Perses ${PERSES_COMMIT}"
git init -q "${WORK_DIR}"
git -C "${WORK_DIR}" remote add origin https://github.com/uw-pluverse/perses.git
git -C "${WORK_DIR}" fetch -q --depth=1 origin "${PERSES_COMMIT}"
git -C "${WORK_DIR}" checkout -q --detach FETCH_HEAD

readonly SFC_TEST_DIR="${WORK_DIR}/sfc/test/org/perses/reduction/reducer/sfc"
readonly PAPER_TEST="${SFC_TEST_DIR}/PaperExampleSimplificationsTest.kt"

test -f "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/StructureFormConverter.kt"
test -f "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/SmallerStructureReplacementReducer.kt"
test -f "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/IdentifierUseEliminationReducer.kt"
test -f "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/StructureCanonicalizationReducer.kt"
test -f "${PAPER_TEST}"

paper_examples="$(grep -c '^  @Test' "${PAPER_TEST}")"
if [[ "${paper_examples}" != "12" ]]; then
  echo "error: expected 12 paper-example tests, found ${paper_examples}" >&2
  exit 3
fi

grep -q 'const val NAME = "sfc_smaller_structure_replacement"' \
  "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/SmallerStructureReplacementReducer.kt"
grep -q 'Algorithm 3 of the SFC paper' \
  "${WORK_DIR}/sfc/src/org/perses/reduction/reducer/sfc/SmallerStructureReplacementReducer.kt"

cd "${WORK_DIR}"
{
  echo "perses_commit=${PERSES_COMMIT}"
  echo "paper_example_tests=${paper_examples}"
  echo "bazel_command=${BAZEL}"
  "${BAZEL}" --version
} | tee "${RESULTS_DIR}/summary.txt"

readonly TARGET_PREFIX="//sfc/test/org/perses/reduction/reducer/sfc"
readonly TARGETS=(
  "${TARGET_PREFIX}:PaperExampleSimplificationsTest"
  "${TARGET_PREFIX}:StructureFormConverterCTest"
  "${TARGET_PREFIX}:SmallerStructureReplacementReducerTest"
  "${TARGET_PREFIX}:IdentifierUseEliminationReducerTest"
  "${TARGET_PREFIX}:StructureCanonicalizationReducerTest"
)

printf 'targets=%s\n' "${TARGETS[*]}" | tee -a "${RESULTS_DIR}/summary.txt"

"${BAZEL}" test \
  --nocache_test_results \
  --test_output=errors \
  "${TARGETS[@]}" 2>&1 | tee "${RESULTS_DIR}/bazel-tests.log"

{
  echo "status=PASS"
  echo "scope=current upstream SFC implementation; 12 paper examples + C converter + three reducer invariant suites"
  echo "reproduction_level=L0 source/provenance audit + scoped L2 mechanism"
  echo "not_claimed=L1,L3"
} | tee -a "${RESULTS_DIR}/summary.txt"

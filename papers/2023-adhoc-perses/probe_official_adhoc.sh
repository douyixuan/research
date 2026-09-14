#!/usr/bin/env bash
set -euo pipefail

PERSES_COMMIT="${PERSES_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${RUNNER_TEMP:-/tmp}/perses-adhoc-${PERSES_COMMIT:0:8}"
OUT="${ROOT}/results/official"

rm -rf "${WORK}" "${OUT}"
mkdir -p "${OUT}"

git clone --filter=blob:none https://github.com/uw-pluverse/perses.git "${WORK}"
git -C "${WORK}" checkout "${PERSES_COMMIT}"

if ! command -v bazelisk >/dev/null 2>&1; then
  command -v go >/dev/null 2>&1 || { echo "Go is required to install Bazelisk" >&2; exit 2; }
  go install github.com/bazelbuild/bazelisk@latest
  export PATH="$(go env GOPATH)/bin:${PATH}"
fi

start_epoch="$(date +%s)"
pushd "${WORK}" >/dev/null
set +e
bazelisk test //test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing \
  --test_output=all \
  --test_timeout=1200 2>&1 | tee "${OUT}/official-system-test.log"
status=${PIPESTATUS[0]}
set -e

if [[ -f bazel-testlogs/test/org/perses/adhoc/system_test_of_adhoc_fuzz_testing/test.log ]]; then
  cp bazel-testlogs/test/org/perses/adhoc/system_test_of_adhoc_fuzz_testing/test.log "${OUT}/bazel-test.log"
fi
popd >/dev/null
end_epoch="$(date +%s)"

{
  echo "perses_commit=${PERSES_COMMIT}"
  echo "bazel_version=$(bazelisk version | head -n 1)"
  echo "java_version=$(java -version 2>&1 | head -n 1)"
  echo "elapsed_seconds=$((end_epoch - start_epoch))"
  echo "test_status=${status}"
  echo "target=//test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing"
} | tee "${OUT}/summary.txt"

exit "${status}"

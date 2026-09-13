#!/usr/bin/env bash
set -euo pipefail

PERSES_COMMIT="${PERSES_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${RUNNER_TEMP:-/tmp}/perses-adhoc-${PERSES_COMMIT:0:8}"
OUT="${ROOT}/results"
CASE_DIR="${WORK}/case"
REDUCED_DIR="${OUT}/reduced"

rm -rf "${WORK}" "${OUT}"
mkdir -p "${CASE_DIR}" "${REDUCED_DIR}"

cp "${ROOT}/case/sample.calc" "${CASE_DIR}/sample.calc"
cp "${ROOT}/case/r.sh" "${CASE_DIR}/r.sh"
chmod +x "${CASE_DIR}/r.sh"

# Sanity-check the original oracle before any upstream build work.
(
  cd "${CASE_DIR}"
  ./r.sh
)

git clone --filter=blob:none https://github.com/uw-pluverse/perses.git "${WORK}/perses"
git -C "${WORK}/perses" checkout "${PERSES_COMMIT}"

if ! command -v bazelisk >/dev/null 2>&1; then
  command -v go >/dev/null 2>&1 || { echo "Go is required to install Bazelisk" >&2; exit 2; }
  go install github.com/bazelbuild/bazelisk@latest
  export PATH="$(go env GOPATH)/bin:${PATH}"
fi

pushd "${WORK}/perses" >/dev/null
bazelisk build \
  //src/org/perses/grammar/adhoc:perses_adhoc_installer_deploy.jar \
  //src/org/perses:perses_deploy.jar \
  2>&1 | tee "${OUT}/bazel-build.log"

installer="${WORK}/perses/bazel-bin/src/org/perses/grammar/adhoc/perses_adhoc_installer_deploy.jar"
perses="${WORK}/perses/bazel-bin/src/org/perses/perses_deploy.jar"

gen_start_ns="$(date +%s%N)"
java -jar "${installer}" \
  --parser-grammar "${ROOT}/grammar/MiniCalc.g4" \
  --start-rule program \
  --token-names-of-identifiers Identifier \
  --package-name org.perses.grammar.adhoc.minicalc \
  --language-kind-yaml-file "${ROOT}/grammar/language_kind.yaml" \
  --enable-pnf-normalization true \
  --output "${OUT}/minicalc.jar" \
  2>&1 | tee "${OUT}/adhoc-compiler.log"
gen_end_ns="$(date +%s%N)"
popd >/dev/null

[[ -s "${OUT}/minicalc.jar" ]]

java -jar "${perses}" \
  --input-file "${CASE_DIR}/sample.calc" \
  --test-script "${CASE_DIR}/r.sh" \
  --language-ext-jars "${OUT}/minicalc.jar" \
  --threads 1 \
  --fully-deterministic-mode true \
  --enable-latra false \
  --enable-vulcan false \
  --enable-trec false \
  --output-dir "${REDUCED_DIR}" \
  --stat-dump-file "${OUT}/perses-stats.txt" \
  2>&1 | tee "${OUT}/perses-run.log"

reduced_file="$(find "${REDUCED_DIR}" -type f -name '*.calc' -print -quit)"
if [[ -z "${reduced_file}" ]]; then
  echo "No reduced .calc file found under ${REDUCED_DIR}" >&2
  find "${REDUCED_DIR}" -maxdepth 3 -type f -print >&2 || true
  exit 3
fi

verify_dir="${WORK}/verify"
mkdir -p "${verify_dir}"
cp "${reduced_file}" "${verify_dir}/sample.calc"
cp "${CASE_DIR}/r.sh" "${verify_dir}/r.sh"
chmod +x "${verify_dir}/r.sh"
(
  cd "${verify_dir}"
  ./r.sh
)

original_statements="$(tr -cd ';' < "${CASE_DIR}/sample.calc" | wc -c | xargs)"
reduced_statements="$(tr -cd ';' < "${reduced_file}" | wc -c | xargs)"
original_bytes="$(wc -c < "${CASE_DIR}/sample.calc" | xargs)"
reduced_bytes="$(wc -c < "${reduced_file}" | xargs)"
generation_ms="$(( (gen_end_ns - gen_start_ns) / 1000000 ))"

[[ "${original_statements}" == "5" ]]
[[ "${reduced_statements}" == "2" ]]

cp "${reduced_file}" "${OUT}/reduced.calc"
{
  echo "paper=Ad Hoc Syntax-Guided Program Reduction"
  echo "level=L0+scoped-L2-current-source"
  echo "perses_commit=${PERSES_COMMIT}"
  echo "original_statements=${original_statements}"
  echo "reduced_statements=${reduced_statements}"
  echo "original_bytes=${original_bytes}"
  echo "reduced_bytes=${reduced_bytes}"
  echo "adhoc_generation_ms=${generation_ms}"
  echo "oracle_preserved=yes"
  echo "dynamic_language_jar_generated=yes"
} | tee "${OUT}/summary.txt"

{
  echo "java=$(java -version 2>&1 | head -n 1)"
  echo "bazel=$(bazelisk version 2>/dev/null | head -n 1 || true)"
  echo "go=$(go version 2>/dev/null || true)"
  echo "runner_os=${RUNNER_OS:-unknown}"
} | tee "${OUT}/environment.txt"

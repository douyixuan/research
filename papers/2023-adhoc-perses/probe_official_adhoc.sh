#!/usr/bin/env bash
set -euo pipefail

PERSES_COMMIT="${PERSES_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${RUNNER_TEMP:-/tmp}/perses-adhoc-${PERSES_COMMIT:0:8}"
CASE_DIR="${WORK}/case"
OUT_DIR="${ROOT}/results/official"

rm -rf "${WORK}" "${OUT_DIR}"
mkdir -p "${CASE_DIR}" "${OUT_DIR}"

git clone --filter=blob:none https://github.com/uw-pluverse/perses.git "${WORK}/perses"
git -C "${WORK}/perses" checkout "${PERSES_COMMIT}"
cp "${ROOT}/case/Tiny.g4" "${CASE_DIR}/Tiny.g4"
cp "${ROOT}/case/language_kind.yaml" "${CASE_DIR}/language_kind.yaml"
cp "${ROOT}/case/program.tiny" "${CASE_DIR}/program.tiny"
cp "${ROOT}/case/r.sh" "${CASE_DIR}/r.sh"
chmod +x "${CASE_DIR}/r.sh"

if ! command -v bazelisk >/dev/null 2>&1; then
  command -v go >/dev/null 2>&1 || { echo "Go is required to install Bazelisk" >&2; exit 2; }
  go install github.com/bazelbuild/bazelisk@latest
  export PATH="$(go env GOPATH)/bin:${PATH}"
fi

pushd "${WORK}/perses" >/dev/null
bazelisk build \
  //src/org/perses/grammar/adhoc:perses_adhoc_installer_deploy.jar \
  //src/org/perses:perses_deploy.jar 2>&1 | tee "${OUT_DIR}/build.log"
INSTALLER="${WORK}/perses/bazel-bin/src/org/perses/grammar/adhoc/perses_adhoc_installer_deploy.jar"
PERSES_JAR="${WORK}/perses/bazel-bin/src/org/perses/perses_deploy.jar"
popd >/dev/null

LANG_JAR="${CASE_DIR}/tiny-language.jar"
install_start=$(date +%s)
java -jar "${INSTALLER}" \
  --parser-grammar "${CASE_DIR}/Tiny.g4" \
  --start-rule program \
  --token-names-of-identifiers IDENT \
  --package-name org.example.tiny \
  --language-kind-yaml-file "${CASE_DIR}/language_kind.yaml" \
  --output "${LANG_JAR}" 2>&1 | tee "${OUT_DIR}/install.log"
install_end=$(date +%s)
test -s "${LANG_JAR}"

run_start=$(date +%s)
pushd "${CASE_DIR}" >/dev/null
# Current Perses enables T-Rec by default. At the pinned 2026 source revision,
# TokenCanonicalizer crashes on EOF for this generated ad-hoc grammar, so this
# paper-mechanism probe disables that later reducer explicitly. The failure is
# retained as toolchain-drift evidence in the first CI run documented in README.
java -jar "${PERSES_JAR}" \
  --test-script "${CASE_DIR}/r.sh" \
  --input-file "${CASE_DIR}/program.tiny" \
  --language-ext-jars "${LANG_JAR}" \
  --enable-trec false 2>&1 | tee "${OUT_DIR}/perses.log"
popd >/dev/null
run_end=$(date +%s)

RESULT="${CASE_DIR}/perses_result/program.tiny"
test -f "${RESULT}"
(
  cd "$(dirname "${RESULT}")"
  "${CASE_DIR}/r.sh"
)

cp "${RESULT}" "${OUT_DIR}/reduced.tiny"
cp "${CASE_DIR}/program.tiny" "${OUT_DIR}/input.tiny"
sha256sum "${LANG_JAR}" > "${OUT_DIR}/language-jar.sha256"

python3 - "${OUT_DIR}" "$((install_end-install_start))" "$((run_end-run_start))" "${PERSES_COMMIT}" "${LANG_JAR}" <<'PY'
import json, pathlib, re, sys
out = pathlib.Path(sys.argv[1])
install_s = int(sys.argv[2])
run_s = int(sys.argv[3])
commit = sys.argv[4]
jar = pathlib.Path(sys.argv[5])
pat = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[=;]")
orig = (out / "input.tiny").read_text()
reduced = (out / "reduced.tiny").read_text()
metrics = {
    "perses_commit": commit,
    "reproduction_level": "official current-source scoped L2",
    "trec_enabled": False,
    "grammar_install_wall_seconds": install_s,
    "reduction_wall_seconds": run_s,
    "language_jar_bytes": jar.stat().st_size,
    "input_bytes": len(orig.encode()),
    "reduced_bytes": len(reduced.encode()),
    "input_lexical_tokens": len(pat.findall(orig)),
    "reduced_lexical_tokens": len(pat.findall(reduced)),
    "property_preserved": True,
    "reduced_program": reduced,
}
assert metrics["reduced_bytes"] < metrics["input_bytes"]
(out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
PY

{
  echo "perses_commit=${PERSES_COMMIT}"
  echo "bazel=$(bazelisk version | head -n 1)"
  echo "java=$(java -version 2>&1 | head -n 1)"
  echo "go=$(go version)"
  echo "runner=$(uname -a)"
  echo "trec_enabled=false"
} > "${OUT_DIR}/environment.txt"

cat "${OUT_DIR}/metrics.json"

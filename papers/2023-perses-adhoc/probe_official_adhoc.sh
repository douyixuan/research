#!/usr/bin/env bash
set -euo pipefail

PERSES_COMMIT="${PERSES_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${RUNNER_TEMP:-/tmp}/perses-adhoc-${PERSES_COMMIT:0:8}"
OUT_DIR="${ROOT}/results/official"
CASE_DIR="${WORK}/case"

rm -rf "${WORK}" "${OUT_DIR}"
mkdir -p "${CASE_DIR}" "${OUT_DIR}"

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
  //src/org/perses:perses_deploy.jar 2>&1 | tee "${OUT_DIR}/build.log"

# Run the upstream end-to-end adhoc language system test as an implementation sanity check.
bazelisk test //test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing \
  --test_output=errors 2>&1 | tee "${OUT_DIR}/upstream-system-test.log"
popd >/dev/null

ADHOC_JAR="${WORK}/perses/bazel-bin/src/org/perses/grammar/adhoc/perses_adhoc_installer_deploy.jar"
PERSES_JAR="${WORK}/perses/bazel-bin/src/org/perses/perses_deploy.jar"
LANG_JAR="${CASE_DIR}/mini_expr.jar"

cp "${ROOT}/case/MiniExpr.g4" "${CASE_DIR}/MiniExpr.g4"
cp "${ROOT}/case/language_kind.yaml" "${CASE_DIR}/language_kind.yaml"
cp "${ROOT}/case/input.mini" "${CASE_DIR}/input.mini"

start_ns=$(date +%s%N)
java -jar "${ADHOC_JAR}" \
  --parser-grammar "${CASE_DIR}/MiniExpr.g4" \
  --start-rule "program" \
  --token-names-of-identifiers "Identifier" \
  --package-name "org.example.perses.adhoc.miniexpr" \
  --language-kind-yaml-file "${CASE_DIR}/language_kind.yaml" \
  --output "${LANG_JAR}" 2>&1 | tee "${OUT_DIR}/grammar-generation.log"
end_ns=$(date +%s%N)
generation_ms=$(( (end_ns - start_ns) / 1000000 ))

test -s "${LANG_JAR}"

cat > "${CASE_DIR}/r.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
grep -q "target" input.mini
EOF
chmod +x "${CASE_DIR}/r.sh"

pushd "${CASE_DIR}" >/dev/null
start_ns=$(date +%s%N)
java -jar "${PERSES_JAR}" \
  --input-file "${CASE_DIR}/input.mini" \
  --test-script "${CASE_DIR}/r.sh" \
  --language-ext-jars "${LANG_JAR}" 2>&1 | tee "${OUT_DIR}/reduction.log"
end_ns=$(date +%s%N)
reduction_ms=$(( (end_ns - start_ns) / 1000000 ))
popd >/dev/null

RESULT_FILE="${CASE_DIR}/perses_result/input.mini"
test -s "${RESULT_FILE}"
grep -q "target" "${RESULT_FILE}"
if grep -Eq 'alpha|beta|gamma|delta' "${RESULT_FILE}"; then
  echo "Unexpected irrelevant statement survived reduction:" >&2
  cat "${RESULT_FILE}" >&2
  exit 3
fi

cp "${RESULT_FILE}" "${OUT_DIR}/reduced.mini"
cp "${ROOT}/case/input.mini" "${OUT_DIR}/original.mini"

GENERATION_MS="${generation_ms}" REDUCTION_MS="${reduction_ms}" PERSES_COMMIT="${PERSES_COMMIT}" \
python3 - "${OUT_DIR}/original.mini" "${OUT_DIR}/reduced.mini" "${OUT_DIR}/summary.json" <<'PY'
import json, os, re, sys
from pathlib import Path
original = Path(sys.argv[1]).read_text()
reduced = Path(sys.argv[2]).read_text()
out = Path(sys.argv[3])
pat = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|;")
summary = {
    "level": "scoped-L2-live-minimal",
    "perses_commit": os.environ["PERSES_COMMIT"],
    "upstream_system_test": "passed",
    "fresh_language": "MiniExpr",
    "grammar_library_generation_ms": int(os.environ["GENERATION_MS"]),
    "reduction_ms": int(os.environ["REDUCTION_MS"]),
    "original_bytes": len(original.encode()),
    "reduced_bytes": len(reduced.encode()),
    "original_token_proxy": len(pat.findall(original)),
    "reduced_token_proxy": len(pat.findall(reduced)),
    "property_preserved": "target" in reduced,
    "irrelevant_identifiers_removed": not any(x in reduced for x in ["alpha", "beta", "gamma", "delta"]),
    "reduced_program": reduced.strip(),
}
out.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

{
  echo "perses_commit=${PERSES_COMMIT}"
  echo "bazelisk=$(bazelisk version | head -n 1)"
  echo "java=$(java -version 2>&1 | head -n 1)"
  echo "grammar_library_generation_ms=${generation_ms}"
  echo "reduction_ms=${reduction_ms}"
} | tee "${OUT_DIR}/environment.txt"

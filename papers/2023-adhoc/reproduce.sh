#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="${ROOT}/results"
PERSES_COMMIT="6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2"
mkdir -p "${RESULTS}"
rm -f "${RESULTS}"/build.log "${RESULTS}"/official-system-test.log \
      "${RESULTS}"/adhoc.log "${RESULTS}"/native.log \
      "${RESULTS}"/adhoc-reduced.test "${RESULTS}"/native-reduced.c \
      "${RESULTS}"/live-summary.json "${RESULTS}"/live-summary.md

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi
if ! command -v java >/dev/null 2>&1; then
  echo "A JDK is required" >&2
  exit 2
fi
if ! command -v bazelisk >/dev/null 2>&1; then
  if command -v go >/dev/null 2>&1; then
    go install github.com/bazelbuild/bazelisk@v1.27.0
    export PATH="$(go env GOPATH)/bin:${PATH}"
  else
    echo "bazelisk is missing; install it or provide Go so the script can install v1.27.0" >&2
    exit 2
  fi
fi

WORK_BASE="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
WORK="${WORK_BASE}/adhoc-perses-repro-${PERSES_COMMIT:0:8}"
rm -rf "${WORK}"
mkdir -p "${WORK}"
trap 'rm -rf "${WORK}"' EXIT

echo "==> Cloning Perses @ ${PERSES_COMMIT}"
git clone --quiet --filter=blob:none https://github.com/uw-pluverse/perses.git "${WORK}/perses"
cd "${WORK}/perses"
git checkout --quiet "${PERSES_COMMIT}"

printf '%s\n' "$(java -version 2>&1 | head -n 1)" > "${RESULTS}/java-version.txt"
printf '%s\n' "$(bazelisk version 2>&1 | head -n 1)" > "${RESULTS}/bazel-version.txt"

echo "==> Building Perses and the ad-hoc grammar installer"
bazelisk build \
  //src/org/perses:perses_deploy.jar \
  //src/org/perses/grammar/adhoc:perses_adhoc_installer_deploy.jar \
  2>&1 | tee "${RESULTS}/build.log"

PERSES_JAR="$(realpath bazel-bin/src/org/perses/perses_deploy.jar)"
ADHOC_COMPILER_JAR="$(realpath bazel-bin/src/org/perses/grammar/adhoc/perses_adhoc_installer_deploy.jar)"
GRAMMAR="$(realpath src/org/perses/grammar/c/OrigC.g4)"
YAML="$(realpath test/org/perses/adhoc/language_kind.yaml)"
EXT_JAR="${WORK}/ext_language.jar"

echo "==> Generating an ad-hoc C grammar library"
GEN_START_NS="$(date +%s%N)"
java -jar "${ADHOC_COMPILER_JAR}" \
  --parser-grammar "${GRAMMAR}" \
  --start-rule "translationUnit" \
  --token-names-of-identifiers "Identifier" \
  --package-name "org.perses.grammar.adhoc.repro2023" \
  --language-kind-yaml-file "${YAML}" \
  --output "${EXT_JAR}" \
  > "${RESULTS}/grammar-generation.log" 2>&1
GEN_END_NS="$(date +%s%N)"
GEN_MS="$(( (GEN_END_NS - GEN_START_NS) / 1000000 ))"
[[ -s "${EXT_JAR}" ]]

run_reduction() {
  local mode="$1"
  local extension="$2"
  local extra_jar="$3"
  local dir="${WORK}/${mode}"
  local input="t.${extension}"
  mkdir -p "${dir}"
  printf 'int var = 0;\n' > "${dir}/${input}"
  cat > "${dir}/oracle.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
grep -q "var" "${input}"
EOF
  chmod +x "${dir}/oracle.sh"

  echo "==> Running ${mode} reduction"
  if [[ -n "${extra_jar}" ]]; then
    (
      cd "${dir}"
      java -jar "${PERSES_JAR}" \
        --test-script "${dir}/oracle.sh" \
        --input-file "${dir}/${input}" \
        --language-ext-jars "${extra_jar}"
    ) > "${RESULTS}/${mode}.log" 2>&1
  else
    (
      cd "${dir}"
      java -jar "${PERSES_JAR}" \
        --test-script "${dir}/oracle.sh" \
        --input-file "${dir}/${input}"
    ) > "${RESULTS}/${mode}.log" 2>&1
  fi

  local reduced="${dir}/perses_result/${input}"
  [[ -s "${reduced}" ]]
  grep -q "var" "${reduced}"
  cp "${reduced}" "${RESULTS}/${mode}-reduced.${extension}"
}

run_reduction "adhoc" "test" "${EXT_JAR}"
run_reduction "native" "c" ""

echo "==> Running the upstream official ad-hoc system test"
bazelisk test //test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing \
  --test_output=errors 2>&1 | tee "${RESULTS}/official-system-test.log"

EXT_SHA256="$(sha256sum "${EXT_JAR}" | awk '{print $1}')"
export RESULTS PERSES_COMMIT GEN_MS EXT_SHA256
python3 - <<'PY'
import hashlib
import json
import os
import re
from pathlib import Path

results = Path(os.environ["RESULTS"])

def token_proxy(text: str) -> int:
    return len(re.findall(r"[A-Za-z_]\w*|\d+|[^\s]", text))

def norm(text: str) -> str:
    return " ".join(text.split())

input_text = "int var = 0;\n"
adhoc = (results / "adhoc-reduced.test").read_text()
native = (results / "native-reduced.c").read_text()
summary = {
    "reproduction_level": "L0 + scoped L2 current-source",
    "upstream_commit": os.environ["PERSES_COMMIT"],
    "grammar_generation_ms": int(os.environ["GEN_MS"]),
    "extension_jar_sha256": os.environ["EXT_SHA256"],
    "input": {
        "bytes": len(input_text.encode()),
        "token_proxy": token_proxy(input_text),
    },
    "adhoc": {
        "bytes": len(adhoc.encode()),
        "token_proxy": token_proxy(adhoc),
        "normalized": norm(adhoc),
    },
    "native": {
        "bytes": len(native.encode()),
        "token_proxy": token_proxy(native),
        "normalized": norm(native),
    },
    "same_normalized_output": norm(adhoc) == norm(native),
    "same_token_proxy": token_proxy(adhoc) == token_proxy(native),
    "official_upstream_system_test": "passed",
}

assert summary["adhoc"]["bytes"] < summary["input"]["bytes"]
assert summary["native"]["bytes"] < summary["input"]["bytes"]
assert "var" in adhoc
assert "var" in native

(results / "live-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
md = [
    "# Live scoped-L2 result",
    "",
    f"- Upstream commit: `{summary['upstream_commit']}`",
    f"- Grammar generation: {summary['grammar_generation_ms']} ms (current machine; not paper-comparable)",
    f"- Input: {summary['input']['bytes']} B / {summary['input']['token_proxy']} token-proxy",
    f"- Ad-hoc: {summary['adhoc']['bytes']} B / {summary['adhoc']['token_proxy']} token-proxy / `{summary['adhoc']['normalized']}`",
    f"- Native: {summary['native']['bytes']} B / {summary['native']['token_proxy']} token-proxy / `{summary['native']['normalized']}`",
    f"- Same normalized output: {summary['same_normalized_output']}",
    f"- Same token proxy: {summary['same_token_proxy']}",
    "- Upstream official ad-hoc system test: passed",
    "",
    "This is a tiny current-source mechanism reproduction, not a reproduction of Tables 2-4 at paper scale.",
]
(results / "live-summary.md").write_text("\n".join(md) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
PY

python3 "${ROOT}/audit_claims.py"
echo "==> Evidence written to ${RESULTS}"

#!/usr/bin/env bash
set -euo pipefail

PPR_COMMIT="${PPR_COMMIT:-6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${RUNNER_TEMP:-/tmp}/perses-ppr-${PPR_COMMIT:0:8}"
CASE_DIR="${WORK}/ppr-case"
OUT_DIR="${ROOT}/results/official"

rm -rf "${WORK}" "${OUT_DIR}"
mkdir -p "${CASE_DIR}" "${OUT_DIR}"

git clone --filter=blob:none https://github.com/uw-pluverse/perses.git "${WORK}/perses"
git -C "${WORK}/perses" checkout "${PPR_COMMIT}"

cp "${ROOT}/case/seed.c" "${CASE_DIR}/seed.c"
cp "${ROOT}/case/variant.c" "${CASE_DIR}/variant.c"
cat > "${CASE_DIR}/r.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
gcc seed.c -O2 -o seed
gcc variant.c -O2 -o variant
[[ "$(./seed)" == "1" ]]
[[ "$(./variant)" == "2" ]]
EOF
chmod +x "${CASE_DIR}/r.sh"

if ! command -v bazelisk >/dev/null 2>&1; then
  command -v go >/dev/null 2>&1 || { echo "Go is required to install Bazelisk" >&2; exit 2; }
  go install github.com/bazelbuild/bazelisk@latest
  export PATH="$(go env GOPATH)/bin:${PATH}"
fi

pushd "${WORK}/perses" >/dev/null
bazelisk run //ppr/src/org/perses/ppr:main -- \
  --input-file "${CASE_DIR}/seed.c" \
  --variant-file "${CASE_DIR}/variant.c" \
  --test-script "${CASE_DIR}/r.sh" \
  --output-dir "${OUT_DIR}" 2>&1 | tee "${OUT_DIR}/official-run.log"
popd >/dev/null

{
  echo "ppr_commit=${PPR_COMMIT}"
  echo "bazel_version=$(bazelisk version | head -n 1)"
  echo "gcc_version=$(gcc --version | head -n 1)"
  echo "output_files:"
  find "${OUT_DIR}" -maxdepth 2 -type f -printf '%P\n' | sort
} | tee "${OUT_DIR}/environment.txt"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/papers/2025-sfc/results"
WORK="${SFC_WORKDIR:-/tmp/perses-sfc-repro}"
PERSes_REPO="https://github.com/uw-pluverse/perses.git"
PERSES_COMMIT="6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2"
mkdir -p "$OUT"
rm -rf "$WORK"

echo "[sfc] cloning official Perses implementation @ $PERSES_COMMIT"
git clone --filter=blob:none "$PERSes_REPO" "$WORK" 2>&1 | tee "$OUT/clone.log"
git -C "$WORK" checkout --detach "$PERSES_COMMIT" 2>&1 | tee -a "$OUT/clone.log"

if command -v bazelisk >/dev/null 2>&1; then
  BAZEL=bazelisk
elif command -v bazel >/dev/null 2>&1; then
  BAZEL=bazel
else
  echo "Neither bazelisk nor bazel is available" >&2
  exit 2
fi

TARGETS=(
  "//sfc/test/org/perses/reduction/reducer/sfc:PaperExampleSimplificationsTest"
  "//sfc/test/org/perses/reduction/reducer/sfc/system_test_smaller_structure:smaller_structure_replacement_reduction_golden_test"
  "//sfc/test/org/perses/reduction/reducer/sfc/system_test_identifier_use_elimination:identifier_use_elimination_reduction_golden_test"
  "//sfc/test/org/perses/reduction/reducer/sfc/system_test_canonicalization:canonicalization_reduction_golden_test"
)

(
  cd "$WORK"
  "$BAZEL" test --test_output=errors "${TARGETS[@]}"
) 2>&1 | tee "$OUT/bazel-test.log"

SRC="$WORK/sfc/test/org/perses/reduction/reducer/sfc/system_test_smaller_structure/t.c"
SSR="$WORK/sfc/test/org/perses/reduction/reducer/sfc/system_test_smaller_structure/golden_reduced_t.c"
IE="$WORK/sfc/test/org/perses/reduction/reducer/sfc/system_test_identifier_use_elimination/golden_reduced_t.c"
SC="$WORK/sfc/test/org/perses/reduction/reducer/sfc/system_test_canonicalization/golden_reduced_t.c"

{
  echo "# SFC scoped L2 evidence"
  echo
  echo "- Perses commit: \`$PERSES_COMMIT\`"
  echo "- Paper-example test: PASS"
  echo "- Smaller Structure Replacement golden test: PASS"
  echo "- Identifier Elimination golden test: PASS"
  echo "- Structure Canonicalization golden test: PASS"
  echo
  echo "## Fixture byte sizes"
  echo
  echo "| fixture | bytes |"
  echo "|---|---:|"
  printf '| original C fixture | %s |\n' "$(wc -c < "$SRC" | tr -d ' ')"
  printf '| SSR golden | %s |\n' "$(wc -c < "$SSR" | tr -d ' ')"
  printf '| IE golden | %s |\n' "$(wc -c < "$IE" | tr -d ' ')"
  printf '| SC golden | %s |\n' "$(wc -c < "$SC" | tr -d ' ')"
  echo
  echo "These fixture sizes are smoke-test evidence only; they are not the paper's benchmark token metrics."
} > "$OUT/summary.md"

cat "$OUT/summary.md"

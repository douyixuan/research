#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_REPO="https://github.com/t3-research/DebugTracker.git"
UPSTREAM_SHA="72798f7f148c4d58ae36055849276cb5571e4047"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$HERE/.work"
UPSTREAM="$WORK/DebugTracker"
RESULTS="$HERE/results"

rm -rf "$WORK" "$RESULTS"
mkdir -p "$WORK" "$RESULTS"

echo "==> Fetch pinned DebugTracker artifact"
git clone --quiet "$UPSTREAM_REPO" "$UPSTREAM"
git -C "$UPSTREAM" checkout --quiet "$UPSTREAM_SHA"
ACTUAL_SHA="$(git -C "$UPSTREAM" rev-parse HEAD)"
[[ "$ACTUAL_SHA" == "$UPSTREAM_SHA" ]]
printf '%s\n' "$ACTUAL_SHA" > "$RESULTS/upstream-commit.txt"

echo "==> Audit paper-visible validation counts"
python3 "$HERE/audit.py" "$UPSTREAM" | tee "$RESULTS/artifact-audit.json"

echo "==> Fresh compile + upstream automated validation"
pushd "$UPSTREAM" >/dev/null
npm ci 2>&1 | tee "$RESULTS/npm-ci.log"
npm test 2>&1 | tee "$RESULTS/npm-test.log"
grep -Fq "DebugTracker unit tests passed." "$RESULTS/npm-test.log"

echo "==> Rebuild VSIX"
npm run package -- --out "$RESULTS/debug-tracker-rebuilt.vsix" 2>&1 | tee "$RESULTS/package.log"
sha256sum debug-tracker-0.1.0.vsix > "$RESULTS/upstream-vsix.sha256"
sha256sum "$RESULTS/debug-tracker-rebuilt.vsix" > "$RESULTS/rebuilt-vsix.sha256"
stat -c '%n %s' debug-tracker-0.1.0.vsix "$RESULTS/debug-tracker-rebuilt.vsix" > "$RESULTS/vsix-sizes.txt"
unzip -l debug-tracker-0.1.0.vsix > "$RESULTS/upstream-vsix-contents.txt"
unzip -l "$RESULTS/debug-tracker-rebuilt.vsix" > "$RESULTS/rebuilt-vsix-contents.txt"

UPSTREAM_BYTES="$(stat -c '%s' debug-tracker-0.1.0.vsix)"
REBUILT_BYTES="$(stat -c '%s' "$RESULTS/debug-tracker-rebuilt.vsix")"
UPSTREAM_ENTRIES="$(unzip -Z1 debug-tracker-0.1.0.vsix | wc -l | tr -d ' ')"
REBUILT_ENTRIES="$(unzip -Z1 "$RESULTS/debug-tracker-rebuilt.vsix" | wc -l | tr -d ' ')"
UPSTREAM_STATE_ENTRIES="$(unzip -Z1 debug-tracker-0.1.0.vsix | grep -c '^extension/\.debugtracker/' || true)"
REBUILT_STATE_ENTRIES="$(unzip -Z1 "$RESULTS/debug-tracker-rebuilt.vsix" | grep -c '^extension/\.debugtracker/' || true)"
cat > "$RESULTS/vsix-packaging-drift.txt" <<EOF
prebuilt_bytes=$UPSTREAM_BYTES
rebuilt_bytes=$REBUILT_BYTES
prebuilt_entries=$UPSTREAM_ENTRIES
rebuilt_entries=$REBUILT_ENTRIES
prebuilt_debugtracker_state_entries=$UPSTREAM_STATE_ENTRIES
rebuilt_debugtracker_state_entries=$REBUILT_STATE_ENTRIES
EOF
cat "$RESULTS/vsix-packaging-drift.txt"
popd >/dev/null

run_task() {
  local name="$1"
  local dir="$2"
  local source="$3"
  local before="$4"
  local after="$5"
  local command="$6"

  echo "==> Sample task: $name (buggy must fail, documented fix must pass)"
  pushd "$UPSTREAM/$dir" >/dev/null

  if [[ "$name" == "typescript" ]]; then
    npm ci > "$RESULTS/${name}-install.log" 2>&1
  fi

  set +e
  bash -lc "$command" > "$RESULTS/${name}-buggy.log" 2>&1
  local buggy_status=$?
  set -e
  if [[ $buggy_status -eq 0 ]]; then
    echo "$name sample unexpectedly passed before the documented fix" >&2
    exit 1
  fi

  python3 - "$source" "$before" "$after" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
before, after = sys.argv[2], sys.argv[3]
text = path.read_text(encoding="utf-8")
if before not in text:
    raise SystemExit(f"expected buggy statement not found in {path}")
path.write_text(text.replace(before, after, 1), encoding="utf-8")
PY

  bash -lc "$command" > "$RESULTS/${name}-fixed.log" 2>&1
  popd >/dev/null
}

run_task \
  "typescript" \
  "sample-tasks/typescript/checkout-pricing" \
  "src/pricing.ts" \
  "const shippingBasisCents = originalSubtotalCents;" \
  "const shippingBasisCents = taxableSubtotalCents;" \
  "npm test"

run_task \
  "python" \
  "sample-tasks/python/checkout-pricing" \
  "src/pricing.py" \
  "shipping_basis_cents = original_subtotal_cents" \
  "shipping_basis_cents = taxable_subtotal_cents" \
  "sh ./run-tests.sh"

run_task \
  "java" \
  "sample-tasks/java/checkout-pricing" \
  "src/debugtracker/checkout/Pricing.java" \
  "int shippingBasisCents = originalSubtotalCents;" \
  "int shippingBasisCents = taxableSubtotalCents;" \
  "sh ./run-tests.sh"

cat > "$RESULTS/summary.md" <<EOF
# DebugTracker reproduction summary

- Upstream commit: \`$UPSTREAM_SHA\`
- Reproduction level: **L0 artifact audit + scoped L2 live-minimal**
- Upstream automated suite: **fresh run passed**
- Paper-visible validation structure: **16 automated checks + 11 manual trial cases** (audited from pinned source/docs)
- VSIX: **fresh package build completed**; committed and rebuilt hashes/sizes/package-state entries are recorded separately
- Cross-language sample bug: TypeScript/Python/Java all **failed before** and **passed after** the documented one-line fix

## Boundary

This CI does **not** execute the 11 GUI/manual cases across Windows, macOS, and Linux, and it does not claim classroom-level effectiveness. It therefore does not reproduce the full manual validation matrix or the paper's future human-study questions.
EOF

cat "$RESULTS/summary.md"

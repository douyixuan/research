#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$HERE/.work"
RESULTS="$HERE/results"
ERWIN="$WORK/Erwin"
PIN="00ed69597b8cfcd0dfff15e86bc22b0ba319134a"

rm -rf "$WORK" "$RESULTS/runtime"
mkdir -p "$WORK" "$RESULTS/runtime"

echo "[1/5] Clone and pin Erwin"
git clone --quiet https://github.com/haoyang9804/Erwin.git "$ERWIN"
git -C "$ERWIN" checkout --quiet "$PIN"

echo "[2/5] Install and build"
cd "$ERWIN"
npm install --no-audit --no-fund
npm run build
npm install --no-save --no-audit --no-fund solc@0.8.20
SOLC="$ERWIN/node_modules/.bin/solcjs"
"$SOLC" --version | tee "$RESULTS/runtime/solc-version.txt"
node --version | tee "$RESULTS/runtime/node-version.txt"
node -e 'console.log(require("./package.json").version)' | tee "$RESULTS/runtime/erwin-version.txt"
git rev-parse HEAD | tee "$RESULTS/runtime/erwin-commit.txt"

echo "[3/5] Run small bounded-exhaustive generation lanes"
for mode in type loc scope; do
  out="$RESULTS/runtime/generated-$mode"
  mkdir -p "$out"
  set +e
  timeout 180 node dist/index.js generate \
    -m "$mode" \
    -max 20 \
    --generation_rounds 1 \
    --out_dir "$out" \
    --refresh_folder \
    >"$RESULTS/runtime/generate-$mode.log" 2>&1
  rc=$?
  set -e
  echo "$rc" > "$RESULTS/runtime/generate-$mode.exitcode"
  if [[ "$rc" -ne 0 && "$rc" -ne 124 ]]; then
    echo "Erwin generation failed for mode=$mode (exit=$rc)" >&2
    tail -100 "$RESULTS/runtime/generate-$mode.log" >&2 || true
    exit "$rc"
  fi
done

echo "[4/5] Compile emitted programs with solcjs 0.8.20"
TOTAL=0
PASS=0
FAIL=0
: > "$RESULTS/runtime/compile-failures.txt"
while IFS= read -r -d '' file; do
  TOTAL=$((TOTAL + 1))
  tmp="$WORK/solc-out-$TOTAL"
  mkdir -p "$tmp"
  if timeout 30 "$SOLC" --bin "$file" -o "$tmp" >"$WORK/compile-$TOTAL.log" 2>&1; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    {
      echo "===== $file ====="
      tail -40 "$WORK/compile-$TOTAL.log" || true
    } >> "$RESULTS/runtime/compile-failures.txt"
  fi
done < <(find "$RESULTS/runtime" -type f -name '*.sol' -print0 | sort -z)

if [[ "$TOTAL" -eq 0 ]]; then
  echo "Erwin produced no Solidity programs" >&2
  exit 1
fi

python3 - "$RESULTS/runtime" "$TOTAL" "$PASS" "$FAIL" <<'PY'
from pathlib import Path
import json, sys
root = Path(sys.argv[1])
total, passed, failed = map(int, sys.argv[2:])
counts = {}
for mode in ("type", "loc", "scope"):
    d = root / f"generated-{mode}"
    counts[mode] = len(list(d.rglob("*.sol"))) if d.exists() else 0
summary = {
    "reproduction_level": "scoped L2 live-minimal",
    "erwin_commit": (root / "erwin-commit.txt").read_text().strip(),
    "erwin_version": (root / "erwin-version.txt").read_text().strip(),
    "node_version": (root / "node-version.txt").read_text().strip(),
    "solcjs_version": (root / "solc-version.txt").read_text().strip(),
    "generated_by_mode": counts,
    "generated_total": total,
    "solcjs_compile_pass": passed,
    "solcjs_compile_fail": failed,
    "compile_pass_rate": passed / total if total else 0.0,
}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
md = [
    "# Erwin scoped L2 runtime summary",
    "",
    f"- Erwin: `{summary['erwin_version']}` @ `{summary['erwin_commit']}`",
    f"- Node: `{summary['node_version']}`",
    f"- solcjs: `{summary['solcjs_version']}`",
    f"- Generated programs: **{total}** (type={counts['type']}, loc={counts['loc']}, scope={counts['scope']})",
    f"- Compile pass/fail: **{passed}/{failed}** ({summary['compile_pass_rate']:.1%} pass)",
    "",
    "This is a small live artifact-health/mechanism run, not a reproduction of the paper's multi-day fuzzing or coverage claims.",
]
(root / "summary.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
PY

echo "[5/5] Done"
cat "$RESULTS/runtime/summary.md"

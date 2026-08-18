#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACT_COMMIT="20d7464201f35c0552777cf7de4d696cb7b1ecd1"
WORK="${RUNNER_TEMP:-/tmp}/oatest-artifact"

rm -rf "$WORK" "$ROOT/results"
mkdir -p "$ROOT/results"

git clone --quiet https://github.com/ShenQingchao/OATest.git "$WORK"
git -C "$WORK" checkout --quiet "$ARTIFACT_COMMIT"

# Structural sanity without importing historical TVM/ORT dependencies.
python -m compileall -q "$WORK/TVM" "$WORK/ORT"

python "$ROOT/audit_artifact.py" "$WORK" --out "$ROOT/results"
{
  echo "artifact_url=https://github.com/ShenQingchao/OATest"
  echo "artifact_commit=$ARTIFACT_COMMIT"
  echo "checked_out_commit=$(git -C "$WORK" rev-parse HEAD)"
  echo "python=$(python --version 2>&1)"
  echo "git=$(git --version)"
} > "$ROOT/results/provenance.txt"

cat "$ROOT/results/report.md"

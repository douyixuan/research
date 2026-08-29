#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
UPSTREAM="$HERE/.matching-source"
COMMIT="c1a11268139ceaaca659bc61346bc843ab1cf874"

rm -rf "$RESULTS" "$UPSTREAM"
mkdir -p "$RESULTS"

python "$HERE/claim_audit.py" --output "$RESULTS/claim-audit.json"
python "$HERE/safe_reproduction.py" --rounds 60 --seed 26041232 \
  --output "$RESULTS/safe-mechanism.json"

git init -q "$UPSTREAM"
git -C "$UPSTREAM" remote add origin https://github.com/FFchopon/TemplateFuzz-LLM.git
git -C "$UPSTREAM" fetch -q --depth 1 origin "$COMMIT"
git -C "$UPSTREAM" checkout -q --detach FETCH_HEAD

# Syntax-only validation: no GPU/model dependencies are installed or imported.
python -m compileall -q "$UPSTREAM"
python "$HERE/audit_source.py" "$UPSTREAM" --commit "$COMMIT" \
  --output "$RESULTS/source-audit.json"

rm -rf "$UPSTREAM"
echo "TemplateFuzz safe reproduction complete."

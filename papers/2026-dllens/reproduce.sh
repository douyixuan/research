#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
PIN="0f617e92c34d60bfdd3bc06d80c17d938879ed9c"
ARTIFACT="${DLLENS_ARTIFACT:-$ROOT/.cache/DLLens}"

if [[ ! -d "$ARTIFACT/.git" ]]; then
  mkdir -p "$(dirname "$ARTIFACT")"
  git clone https://github.com/maybeLee/DLLens.git "$ARTIFACT"
fi

git -C "$ARTIFACT" fetch --quiet origin "$PIN"
git -C "$ARTIFACT" checkout --quiet --detach "$PIN"

python3 "$ROOT/papers/2026-dllens/reproduce.py" "$ARTIFACT" \
  --output "$ROOT/papers/2026-dllens/results"

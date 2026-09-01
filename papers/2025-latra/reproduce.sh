#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$ROOT/.work"
RESULTS="$ROOT/results"
ARTIFACT_SHA="7a9e619b74c11418f5c5d9b469227153b674d8a5"
PERSES_SHA="6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2"
BAZELISK_VERSION="v1.29.0"
MODE="${1:---all}"

case "$MODE" in
  --all|--l1|--l2) ;;
  *) echo "usage: $0 [--all|--l1|--l2]" >&2; exit 2 ;;
esac

rm -rf "$WORK" "$RESULTS"
mkdir -p "$WORK/bin" "$RESULTS"

fetch_repo() {
  local url="$1"
  local sha="$2"
  local dst="$3"
  git init -q "$dst"
  git -C "$dst" remote add origin "$url"
  git -C "$dst" fetch -q --depth 1 origin "$sha"
  git -C "$dst" checkout -q FETCH_HEAD
}

if [[ "$MODE" == "--all" || "$MODE" == "--l1" ]]; then
  echo "== L1: recompute published artifact outputs =="
  fetch_repo \
    https://github.com/uw-pluverse/latra-artifact.git \
    "$ARTIFACT_SHA" \
    "$WORK/latra-artifact"
  python3 "$ROOT/recompute.py" "$WORK/latra-artifact/benchmark" \
    | tee "$RESULTS/l1-report.json"
fi

if [[ "$MODE" == "--all" || "$MODE" == "--l2" ]]; then
  echo "== scoped L2: fresh current-source Latra tests =="
  fetch_repo \
    https://github.com/uw-pluverse/perses.git \
    "$PERSES_SHA" \
    "$WORK/perses"

  curl -fsSLo "$WORK/bin/bazelisk" \
    "https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-amd64"
  curl -fsSLo "$WORK/bin/bazelisk.sha256" \
    "https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-amd64.sha256"
  expected_sha="$(awk '{print $1}' "$WORK/bin/bazelisk.sha256")"
  actual_sha="$(sha256sum "$WORK/bin/bazelisk" | awk '{print $1}')"
  [[ "$actual_sha" == "$expected_sha" ]] || {
    echo "Bazelisk checksum mismatch: expected $expected_sha got $actual_sha" >&2
    exit 1
  }
  chmod +x "$WORK/bin/bazelisk"

  set +e
  (
    cd "$WORK/perses"
    "$WORK/bin/bazelisk" test \
      //latra/test/org/perses/reduction/reducer/latra:FullFunctionalLatraRewriterBuilderTest \
      //latra/test/org/perses/reduction/reducer/latra:CLatraTransformationTest \
      //latra/test/org/perses/reduction/reducer/latra:SMTLatraTransformationTest \
      --test_output=errors \
      --noshow_progress
  ) 2>&1 | tee "$RESULTS/l2-bazel.log"
  bazel_status=${PIPESTATUS[0]}
  set -e

  python3 - "$PERSES_SHA" "$BAZELISK_VERSION" "$bazel_status" > "$RESULTS/l2-report.json" <<'PY'
import json
import sys

perses_sha, bazelisk_version, status = sys.argv[1], sys.argv[2], int(sys.argv[3])
print(json.dumps({
    "level": "scoped L2 current-source mechanism probe",
    "perses_commit": perses_sha,
    "bazelisk_version": bazelisk_version,
    "tests": [
        "FullFunctionalLatraRewriterBuilderTest",
        "CLatraTransformationTest",
        "SMTLatraTransformationTest",
    ],
    "passed": status == 0,
}, indent=2, sort_keys=True))
PY

  exit "$bazel_status"
fi

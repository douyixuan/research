#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PAPER_DIR="$ROOT/papers/2026-repotrace"
RESULTS="$PAPER_DIR/results"
WORK="$PAPER_DIR/.work"
UPSTREAM="$WORK/RepoTrace"
UPSTREAM_REPO="https://github.com/t3-research/RepoTrace.git"
UPSTREAM_SHA="60e59177dd0a1621108c3b1aaeb2a93e447f0a3e"
DB_PATH="$WORK/repotrace.db"
PORT=4017

rm -rf "$RESULTS" "$WORK"
mkdir -p "$RESULTS" "$WORK"

{
  echo "RepoTrace reproduction"
  echo "upstream=$UPSTREAM_REPO"
  echo "sha=$UPSTREAM_SHA"
  echo "node=$(node --version)"
  echo "npm=$(npm --version)"
} | tee "$RESULTS/environment.txt"

git clone --quiet "$UPSTREAM_REPO" "$UPSTREAM"
git -C "$UPSTREAM" checkout --quiet "$UPSTREAM_SHA"

# Audit the exact public GitHub snapshot against its own reproducibility manifest.
{
  test -d "$UPSTREAM/paper" && echo "paper_dir_present=true" || echo "paper_dir_present=false"
  test -f "$UPSTREAM/paper/supporting/VALIDATION_NOTES.md" && echo "validation_notes_present=true" || echo "validation_notes_present=false"
  test -f "$UPSTREAM/PROJECT_PLAN.md" && echo "project_plan_present=true" || echo "project_plan_present=false"
} | tee "$RESULTS/artifact-audit.txt"

cd "$UPSTREAM"
npm ci 2>&1 | tee "$RESULTS/npm-ci.log"
npm test 2>&1 | tee "$RESULTS/npm-test.log"
npm run typecheck 2>&1 | tee "$RESULTS/typecheck.log"
npm run build 2>&1 | tee "$RESULTS/build.log"

REPOTRACE_DB_PATH="$DB_PATH" npm run db:seed-demo 2>&1 | tee "$RESULTS/seed-demo.log"

PORT="$PORT" REPOTRACE_DB_PATH="$DB_PATH" npm run dev:server >"$RESULTS/server.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >"$RESULTS/health.json"; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:${PORT}/health" >"$RESULTS/health.json"
curl -fsS "http://127.0.0.1:${PORT}/api/export/json" >"$RESULTS/export.json"
curl -fsS "http://127.0.0.1:${PORT}/api/projects/1/backup" >"$RESULTS/project-backup.json"

python3 - "$RESULTS" "$UPSTREAM_SHA" <<'PY'
import json, pathlib, re, sys
out = pathlib.Path(sys.argv[1])
sha = sys.argv[2]
raw_log = (out / "npm-test.log").read_text(errors="replace")
# GitHub logs preserve Vitest ANSI styling, so strip escape sequences before parsing.
ansi = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
log = ansi.sub("", raw_log)
m = re.search(r"Tests\s+(\d+)\s+passed", log)
passed = int(m.group(1)) if m else None
health = json.loads((out / "health.json").read_text())
export = json.loads((out / "export.json").read_text())
audit = dict(
    line.split("=", 1) for line in (out / "artifact-audit.txt").read_text().splitlines()
)

def size(value):
    return len(value) if isinstance(value, list) else None

summary = {
    "upstream_sha": sha,
    "vitest_passed": passed,
    "paper_reported_test_count": 37,
    "test_count_matches_paper": passed == 37,
    "health": health,
    "seeded_export_top_level_keys": sorted(export.keys()) if isinstance(export, dict) else [],
    "seeded_records": size(export.get("records")) if isinstance(export, dict) else None,
    "seeded_snapshots": size(export.get("snapshots")) if isinstance(export, dict) else None,
    "seeded_annotations": size(export.get("annotations")) if isinstance(export, dict) else None,
    "artifact_audit": audit,
    "paper_validation_claims": {
        "records": 20,
        "snapshots": 22,
        "comments": 38,
        "notes": 20,
        "annotations": 98,
        "screening_reviews": 20,
        "fix_evidence": 20,
        "simulated_consensus_conflicts": 4,
    },
    "paper_validation_recomputed": False,
    "paper_validation_recompute_blocker": "public GitHub snapshot references paper/supporting/VALIDATION_NOTES.md but does not contain paper/; seeded demo is explicitly not the full 20-record validation dataset",
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if passed != 37:
    raise SystemExit(f"expected 37 upstream tests, parsed {passed!r}")
if health.get("status") != "ok":
    raise SystemExit(f"health check failed: {health}")
PY

cleanup
trap - EXIT

echo "RepoTrace scoped L2 reproduction passed. Evidence: $RESULTS/summary.json"

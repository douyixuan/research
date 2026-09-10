#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

def read_int(name: str) -> int:
    return int((RESULTS / name).read_text().strip())

n = read_int("nocache.oracle-count")
r = read_int("rcc.oracle-count")
no_text = (RESULTS / "nocache.c").read_text()
rcc_text = (RESULTS / "rcc.c").read_text()
input_bytes = (ROOT / "case" / "small.c").stat().st_size
no_bytes = (RESULTS / "nocache.c").stat().st_size
rcc_bytes = (RESULTS / "rcc.c").stat().st_size

if r > n:
    raise SystemExit(f"unexpected: RCC oracle calls {r} > no-cache {n}")

summary = {
    "level": "scoped L2 current-release Perses probe; not paper-scale L3 and not L1",
    "perses_release": "v2.7",
    "perses_sha256": "1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427",
    "input_bytes": input_bytes,
    "no_cache_oracle_calls": n,
    "rcc_oracle_calls": r,
    "oracle_calls_avoided": n - r,
    "oracle_call_reduction_pct": round(100.0 * (n - r) / n, 2) if n else 0.0,
    "no_cache_reduced_bytes": no_bytes,
    "rcc_reduced_bytes": rcc_bytes,
    "same_reduced_text": no_text == rcc_text,
    "configuration": {
        "nocache": "--edit-caching false --query-caching false",
        "rcc": "--query-caching true --query-cache-type COMPACT_QUERY_CACHE",
        "threads": 1,
        "other_reducers_disabled": ["vulcan", "latra", "sfc", "lpr", "trec"],
    },
    "oracle": "gcc -O0 compile + process exit code == 12",
}
(RESULTS / "live-perses-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))

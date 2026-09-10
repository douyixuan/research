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
    "level": "scoped L2 official RCC implementation probe on Perses v1.9; only valid if this manual run completes",
    "perses_release": "v1.9",
    "release_asset_size_bytes": 70349824,
    "toolchain_drift": "Perses v2.7 removed the public --query-cache-type selector; v1.9 still exposes COMPACT_QUERY_CACHE",
    "input_bytes": input_bytes,
    "no_cache_oracle_calls": n,
    "rcc_oracle_calls": r,
    "oracle_calls_avoided": n - r,
    "oracle_call_reduction_pct": round(100.0 * (n - r) / n, 2) if n else 0.0,
    "no_cache_reduced_bytes": no_bytes,
    "rcc_reduced_bytes": rcc_bytes,
    "same_reduced_text": no_text == rcc_text,
    "configuration": {
        "nocache": "--query-caching FALSE",
        "rcc": "--query-caching TRUE --query-cache-type COMPACT_QUERY_CACHE",
        "threads": 1,
    },
    "oracle": "gcc -O0 compile + process exit code == 12",
}
(RESULTS / "live-perses-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))

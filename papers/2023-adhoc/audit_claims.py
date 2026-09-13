#!/usr/bin/env python3
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

# Values transcribed from Tables 1-4 of the 5-page FSE'23 tool paper.
loc_parts = [89, 3, 67, 33]
native_tokens = [98, 144, 153, 328, 51]
adhoc_tokens = [98, 144, 153, 328, 51]
native_time = [917, 756, 1527, 2701, 56]
adhoc_time = [926, 789, 1725, 2611, 57]
grammar_generation = [2.483, 8.679, 8.684, 14.356, 14.648, 15.672]

summary = {
    "table1_loc_sum": sum(loc_parts),
    "table2_native_mean_tokens": mean(native_tokens),
    "table2_adhoc_mean_tokens": mean(adhoc_tokens),
    "table2_all_equal": native_tokens == adhoc_tokens,
    "table3_native_mean_seconds": mean(native_time),
    "table3_adhoc_mean_seconds": mean(adhoc_time),
    "table3_overhead_percent": (mean(adhoc_time) / mean(native_time) - 1.0) * 100.0,
    "table4_generation_mean_seconds": mean(grammar_generation),
}

assert summary["table1_loc_sum"] == 192
assert summary["table2_native_mean_tokens"] == 154.8
assert summary["table2_adhoc_mean_tokens"] == 154.8
assert summary["table2_all_equal"]
assert round(summary["table3_native_mean_seconds"]) == 1191
assert round(summary["table3_adhoc_mean_seconds"]) == 1222
assert 2.5 < summary["table3_overhead_percent"] < 2.6
assert 10.7 < summary["table4_generation_mean_seconds"] < 10.8

(RESULTS / "paper-claim-audit.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

print(json.dumps(summary, indent=2, sort_keys=True))
print("NOTE: arithmetic audit only (L0), not artifact reprocessing/L1.")

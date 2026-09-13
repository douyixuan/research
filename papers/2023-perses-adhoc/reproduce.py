#!/usr/bin/env python3
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "published_tables.json").read_text())
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

# Table 1: published per-file LOC add up to 192, while surrounding prose says ~190/200.
loc_sum = sum(DATA["table1_glsl_infrastructure_lines"].values())

# Table 2: effectiveness.
t2 = DATA["table2_effectiveness"]
original_mean = mean(r["original_tokens"] for r in t2)
perses_mean = mean(r["perses_tokens"] for r in t2)
adhoc_mean = mean(r["adhoc_tokens"] for r in t2)
identical_cases = sum(r["perses_tokens"] == r["adhoc_tokens"] for r in t2)

# Table 3: reduction time / speed.
t3 = DATA["table3_efficiency"]
perses_time_mean = mean(r["perses_time_s"] for r in t3)
adhoc_time_mean = mean(r["adhoc_time_s"] for r in t3)
perses_speed_mean = mean(r["perses_speed_tok_s"] for r in t3)
adhoc_speed_mean = mean(r["adhoc_speed_tok_s"] for r in t3)
slowdown_pct = (adhoc_time_mean / perses_time_mean - 1.0) * 100.0

# Table 4: one-time grammar-library generation cost.
t4 = DATA["table4_grammar_generation"]
generation_mean = mean(r["time_s"] for r in t4)
generation_max = max(t4, key=lambda r: r["time_s"])

summary = {
    "level": "L1-partial-published-table-recalculation",
    "table1": {
        "sum_of_listed_lines": loc_sum,
        "paper_abstract_claim_approx_lines": 190,
        "paper_section_claim_approx_lines": 200,
        "note": "The listed rows sum to 192; the paper uses both 190 and 200 in surrounding prose."
    },
    "table2": {
        "original_tokens_mean": original_mean,
        "perses_tokens_mean": perses_mean,
        "adhoc_tokens_mean": adhoc_mean,
        "identical_reduced_token_count_cases": identical_cases,
        "case_count": len(t2)
    },
    "table3": {
        "perses_time_mean_s": perses_time_mean,
        "adhoc_time_mean_s": adhoc_time_mean,
        "adhoc_time_slowdown_pct": slowdown_pct,
        "perses_speed_mean_tokens_s": perses_speed_mean,
        "adhoc_speed_mean_tokens_s": adhoc_speed_mean
    },
    "table4": {
        "grammar_generation_mean_s": generation_mean,
        "slowest_language": generation_max["language"],
        "slowest_generation_s": generation_max["time_s"]
    }
}

# Match the paper's displayed rounding, without pretending this is a fresh rerun.
assert original_mean == 29764
assert round(perses_mean) == 155
assert round(adhoc_mean) == 155
assert identical_cases == 5
assert round(perses_time_mean) == 1191
assert round(adhoc_time_mean) == 1222
assert round(slowdown_pct, 1) == 2.5 or round(slowdown_pct, 1) == 2.6
assert round(perses_speed_mean, 3) == 43.048
assert round(adhoc_speed_mean, 3) == 41.828
assert 10.0 < generation_mean < 11.0
assert generation_max["language"] == "Java"
assert generation_max["time_s"] == 15.672
assert loc_sum == 192

(OUT / "l1-summary.json").write_text(json.dumps(summary, indent=2) + "\n")

print(json.dumps(summary, indent=2))

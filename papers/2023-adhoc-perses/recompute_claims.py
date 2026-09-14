#!/usr/bin/env python3
import json
from pathlib import Path

subjects = ["clang-23353", "clang-22382", "gcc-65383", "gcc-66186", "gcc-71626"]
original_tokens = [30196, 21068, 43942, 47481, 6133]
perses_tokens = [98, 144, 153, 328, 51]
adhoc_tokens = [98, 144, 153, 328, 51]
perses_time = [917, 756, 1527, 2701, 56]
adhoc_time = [926, 789, 1725, 2611, 57]
perses_speed = [32.82, 27.67, 28.68, 17.46, 108.61]
adhoc_speed = [32.50, 26.51, 25.38, 18.05, 106.70]
grammar_times = {
    "JSON": 2.483,
    "C": 8.679,
    "Scala": 8.684,
    "Rust": 14.356,
    "C++": 14.648,
    "Java": 15.672,
}

def mean(xs):
    return sum(xs) / len(xs)

result = {
    "source": "ESEC/FSE 2023 paper Tables 2-4; arithmetic audit only",
    "subjects": subjects,
    "effectiveness": {
        "all_final_token_counts_equal": perses_tokens == adhoc_tokens,
        "mean_original_tokens": mean(original_tokens),
        "mean_perses_tokens": mean(perses_tokens),
        "mean_adhoc_tokens": mean(adhoc_tokens),
    },
    "efficiency": {
        "mean_perses_seconds": mean(perses_time),
        "mean_adhoc_seconds": mean(adhoc_time),
        "adhoc_time_overhead_percent": (mean(adhoc_time) / mean(perses_time) - 1.0) * 100.0,
        "mean_perses_speed_tokens_per_second": mean(perses_speed),
        "mean_adhoc_speed_tokens_per_second": mean(adhoc_speed),
    },
    "grammar_generation": {
        "times_seconds": grammar_times,
        "mean_seconds": mean(list(grammar_times.values())),
        "max_language": max(grammar_times, key=grammar_times.get),
        "max_seconds": max(grammar_times.values()),
    },
    "reproduction_level_note": "This is not L1: values are transcribed from the paper, not reprocessed from released historical experiment outputs.",
}

out = Path(__file__).resolve().parent / "results" / "paper_claims.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""Arithmetic audit of selected TemplateFuzz paper-reported values.

This is not a model experiment and therefore counts only as L0 claim auditing.
"""
import argparse
import json
from pathlib import Path

PAPER = {
    "overall_top1_asr": 90.5,
    "overall_top5_asr": 98.2,
    "top1_advantage_pp": {"ChatBug": 47.9, "GPTFuzzer": 21.3, "TurboFuzzLLM": 22.1},
    "top5_advantage_pp": {"ChatBug": 47.0, "GPTFuzzer": 9.1, "TurboFuzzLLM": 14.3},
    "heuristic_ablation": {
        "TemplateFuzz": {"top1": 95.58, "top5": 100.0, "acc_delta": 0.21},
        "no_sample": {"top1": 87.88, "top5": 100.0, "acc_delta": -1.60},
        "random": {"top1": 74.04, "top5": 86.35, "acc_delta": -2.01},
        "genetic": {"top1": 83.27, "top5": 98.08, "acc_delta": -2.53},
    },
    "judge": {
        "original_rule": {"accuracy": 83.46, "tpr": 78.08, "fpr": 11.15},
        "model": {"accuracy": 89.42, "tpr": 97.50, "fpr": 2.53, "seconds": 1425},
        "enhanced_rule": {"accuracy": 88.27, "tpr": 92.69, "fpr": 8.02, "seconds_lt": 1},
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    inferred = {
        "top1_baseline_average": {k: round(PAPER["overall_top1_asr"] - v, 1) for k, v in PAPER["top1_advantage_pp"].items()},
        "top5_baseline_average": {k: round(PAPER["overall_top5_asr"] - v, 1) for k, v in PAPER["top5_advantage_pp"].items()},
        "heuristic_top1_gain_pp": {
            k: round(PAPER["heuristic_ablation"]["TemplateFuzz"]["top1"] - row["top1"], 2)
            for k, row in PAPER["heuristic_ablation"].items() if k != "TemplateFuzz"
        },
        "judge_accuracy_gap_pp": round(PAPER["judge"]["model"]["accuracy"] - PAPER["judge"]["enhanced_rule"]["accuracy"], 2),
        "judge_runtime_speedup_lower_bound": PAPER["judge"]["model"]["seconds"],
    }

    assert inferred["judge_accuracy_gap_pp"] == 1.15
    assert inferred["heuristic_top1_gain_pp"]["random"] == 21.54
    assert inferred["heuristic_top1_gain_pp"]["genetic"] == 12.31
    assert inferred["heuristic_top1_gain_pp"]["no_sample"] == 7.70

    result = {
        "level": "L0 claim arithmetic audit",
        "paper_reported": PAPER,
        "derived_checks": inferred,
        "note": "No paper raw outputs or model inference are used here.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inferred, indent=2))


if __name__ == "__main__":
    main()

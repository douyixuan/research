#!/usr/bin/env python3
"""Recompute Latra's released headline results from the pinned official artifact."""

from __future__ import annotations

import csv
import io
import json
import statistics
import urllib.request
from pathlib import Path

ARTIFACT_COMMIT = "7a9e619b74c11418f5c5d9b469227153b674d8a5"
BASE = f"https://raw.githubusercontent.com/uw-pluverse/latra-artifact/{ARTIFACT_COMMIT}/benchmark"
FILES = {
    "c": "c-benchmark.csv",
    "smt_tokens": "smt-tokens.csv",
    "smt_time": "smt-time.csv",
    "smt_queries": "smt-queries.csv",
}
RESULTS = Path(__file__).with_name("results")


def fetch_csv(name: str) -> list[dict[str, str]]:
    url = f"{BASE}/{FILES[name]}"
    with urllib.request.urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def mean(rows: list[dict[str, str]], column: str) -> float:
    return statistics.mean(float(r[column]) for r in rows)


def avg_relative_gain(rows: list[dict[str, str]], baseline: str, treatment: str) -> float:
    return statistics.mean(
        (float(r[baseline]) - float(r[treatment])) / float(r[baseline]) * 100.0
        for r in rows
    )


def assert_close(actual: float, expected: float, tolerance: float = 0.02) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"expected {expected:.2f}, got {actual:.4f}")


def main() -> None:
    c_rows = fetch_csv("c")
    smt_tokens = fetch_csv("smt_tokens")
    smt_time = fetch_csv("smt_time")
    smt_queries = fetch_csv("smt_queries")

    report = {
        "artifact_commit": ARTIFACT_COMMIT,
        "level": "L1-reported-results",
        "c_cases": len(c_rows),
        "smt_cases": len(smt_tokens),
        "c": {
            "mean_tokens_vulcan": mean(c_rows, "Vulcan"),
            "mean_tokens_creduce": mean(c_rows, "C-Reduce"),
            "mean_tokens_latra": mean(c_rows, "Latra"),
            "avg_per_case_token_gain_vs_vulcan_pct": avg_relative_gain(c_rows, "Vulcan", "Latra"),
        },
        "smt": {
            "mean_tokens_vulcan": mean(smt_tokens, "Vulcan"),
            "mean_tokens_ddsmt": mean(smt_tokens, "ddSMT"),
            "mean_tokens_latra": mean(smt_tokens, "Latra"),
            "avg_per_case_token_gain_vs_vulcan_pct": avg_relative_gain(smt_tokens, "Vulcan", "Latra"),
            "avg_per_case_time_gain_vs_vulcan_pct": avg_relative_gain(smt_time, "Vulcan", "Latra"),
            "mean_queries_vulcan": mean(smt_queries, "Vulcan"),
            "mean_queries_ddsmt": mean(smt_queries, "ddSMT"),
            "mean_queries_latra": mean(smt_queries, "Latra"),
        },
    }

    # Headline numbers reported in the ASE 2025 paper/artifact README.
    assert len(c_rows) == 20
    assert len(smt_tokens) == 205
    assert_close(report["c"]["avg_per_case_token_gain_vs_vulcan_pct"], 33.77)
    assert round(report["c"]["mean_tokens_latra"]) == 89
    assert round(report["c"]["mean_tokens_creduce"]) == 85
    assert_close(report["smt"]["avg_per_case_token_gain_vs_vulcan_pct"], 9.17)
    assert round(report["smt"]["mean_tokens_latra"]) == 103
    assert round(report["smt"]["mean_tokens_ddsmt"]) == 109
    assert_close(report["smt"]["avg_per_case_time_gain_vs_vulcan_pct"], 32.27)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "l1-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

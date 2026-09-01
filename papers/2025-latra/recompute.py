#!/usr/bin/env python3
import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean_col(rows, column):
    return statistics.mean(float(row[column]) for row in rows)


def mean_relative_improvement(rows, baseline, candidate):
    values = []
    for row in rows:
        base = float(row[baseline])
        cand = float(row[candidate])
        if base == 0:
            raise ValueError(f"zero baseline for {row.get('Bug', '<unknown>')}")
        values.append((base - cand) / base * 100.0)
    return statistics.mean(values)


def exact_two_sided_sign_test(rows, a, b):
    diffs = [float(row[a]) - float(row[b]) for row in rows]
    positive = sum(diff > 0 for diff in diffs)
    negative = sum(diff < 0 for diff in diffs)
    ties = len(diffs) - positive - negative
    n = positive + negative
    if n == 0:
        p_value = 1.0
    else:
        k = min(positive, negative)
        lower_tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
        p_value = min(1.0, 2.0 * lower_tail)
    return {
        "a_greater_than_b": positive,
        "a_less_than_b": negative,
        "ties": ties,
        "two_sided_p": p_value,
    }


def ids(rows):
    return [row["Bug"] for row in rows]


def assert_close(actual, expected, tolerance, label):
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{label}: expected {expected} +/- {tolerance}, got {actual}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_dir", type=Path)
    args = parser.parse_args()

    c_rows = load_csv(args.benchmark_dir / "c-benchmark.csv")
    smt_tokens = load_csv(args.benchmark_dir / "smt-tokens.csv")
    smt_queries = load_csv(args.benchmark_dir / "smt-queries.csv")
    smt_time = load_csv(args.benchmark_dir / "smt-time.csv")

    if len(c_rows) != 20:
        raise AssertionError(f"expected 20 C subjects, got {len(c_rows)}")
    if not (len(smt_tokens) == len(smt_queries) == len(smt_time) == 205):
        raise AssertionError(
            "expected 205 aligned SMT subjects, got "
            f"tokens={len(smt_tokens)}, queries={len(smt_queries)}, time={len(smt_time)}"
        )
    if ids(smt_tokens) != ids(smt_queries) or ids(smt_tokens) != ids(smt_time):
        raise AssertionError("SMT result tables do not contain subjects in the same order")

    c_improvement = mean_relative_improvement(c_rows, "Vulcan", "Latra")
    smt_improvement = mean_relative_improvement(smt_tokens, "Vulcan", "Latra")

    report = {
        "level": "L1 partial: re-analysis of author-produced outputs",
        "c": {
            "subjects": len(c_rows),
            "mean_tokens": {
                "Vulcan": mean_col(c_rows, "Vulcan"),
                "C-Reduce": mean_col(c_rows, "C-Reduce"),
                "Latra": mean_col(c_rows, "Latra"),
            },
            "mean_relative_token_improvement_latra_vs_vulcan_pct": c_improvement,
            "latra_vs_c_reduce_sign_test": exact_two_sided_sign_test(
                c_rows, "Latra", "C-Reduce"
            ),
        },
        "smt": {
            "subjects": len(smt_tokens),
            "mean_tokens": {
                "Vulcan": mean_col(smt_tokens, "Vulcan"),
                "ddSMT": mean_col(smt_tokens, "ddSMT"),
                "Latra": mean_col(smt_tokens, "Latra"),
            },
            "mean_relative_token_improvement_latra_vs_vulcan_pct": smt_improvement,
            "mean_queries": {
                "Vulcan": mean_col(smt_queries, "Vulcan"),
                "ddSMT": mean_col(smt_queries, "ddSMT"),
                "Latra": mean_col(smt_queries, "Latra"),
            },
            "mean_time_seconds": {
                "Vulcan": mean_col(smt_time, "Vulcan"),
                "ddSMT": mean_col(smt_time, "ddSMT"),
                "Latra": mean_col(smt_time, "Latra"),
            },
        },
    }

    # Headline paper values. These checks intentionally fail if the public artifact drifts.
    assert_close(c_improvement, 33.77, 0.01, "C relative token improvement")
    assert_close(smt_improvement, 9.17, 0.01, "SMT relative token improvement")
    assert_close(report["c"]["mean_tokens"]["Latra"], 89.0, 0.6, "C Latra mean tokens")
    assert_close(report["c"]["mean_tokens"]["C-Reduce"], 85.0, 0.6, "C-Reduce mean tokens")
    assert_close(report["smt"]["mean_tokens"]["Latra"], 103.0, 0.6, "SMT Latra mean tokens")
    assert_close(report["smt"]["mean_tokens"]["ddSMT"], 109.0, 0.6, "ddSMT mean tokens")

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

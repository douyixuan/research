#!/usr/bin/env python3
"""Recompute SFC minimization results from the pinned official artifact.

This is L1 only: it reprocesses authors' released result CSVs. It does not rerun
Perses/Vulcan/SFC on fresh programs.
"""

from __future__ import annotations

import json
import math
import statistics
import urllib.request
from pathlib import Path

ARTIFACT_REPO = "sfc-reducer/sfc-reducer"
ARTIFACT_COMMIT = "ccf633861cdda312f5f6a6fba8a68f08cfa93888"
BASE = f"https://raw.githubusercontent.com/{ARTIFACT_REPO}/{ARTIFACT_COMMIT}/benchmark/results_csv"
RESULTS = Path(__file__).with_name("results")

LANG = {
    "c": {
        "perses": "perses_results.csv",
        "sfc_perses": "proj_results.csv",
        "vulcan": "vulcan_results.csv",
        "sfc_vulcan": "proj_after_vulcan_results.csv",
        "sfc_perses_time_includes_baseline": True,
        "time_aggregate": "arithmetic",
        "expected_cases": 20,
    },
    "rust": {
        "perses": "perses_results.csv",
        "sfc_perses": "proj_after_perses_results.csv",
        "vulcan": "vulcan_results.csv",
        "sfc_vulcan": "proj_after_vulcan_results.csv",
        "sfc_perses_time_includes_baseline": False,
        "time_aggregate": "arithmetic",
        "expected_cases": 20,
    },
    "smt": {
        "perses": "perses_results.csv",
        "sfc_perses": "proj_after_perses_results.csv",
        "vulcan": "vulcan_results.csv",
        "sfc_vulcan": "proj_after_vulcan_results.csv",
        "sfc_perses_time_includes_baseline": False,
        "time_aggregate": "geometric",
        "expected_cases": 205,
    },
}

# Main-text RQ1 values from the paper. The abstract contains a conflicting
# SFCPerses/SMT time ratio (1.42x); 1.42x is the main-text SFCVulcan/SMT value.
PAPER = {
    "c": {"sfc_perses_reduction_pct": 36.82, "sfc_vulcan_reduction_pct": 14.51,
          "sfc_perses_time_x": 3.65, "sfc_vulcan_time_x": 1.56},
    "rust": {"sfc_perses_reduction_pct": 18.71, "sfc_vulcan_reduction_pct": 7.65,
             "sfc_perses_time_x": 16.99, "sfc_vulcan_time_x": 2.35},
    "smt": {"sfc_perses_reduction_pct": 41.05, "sfc_vulcan_reduction_pct": 7.66,
            "sfc_perses_time_x": 3.97, "sfc_vulcan_time_x": 1.42},
}


def fetch(path: str) -> str:
    url = path
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8")


def parse(text: str) -> dict[str, tuple[int, int]]:
    """Match the official plotting scripts: field 2=time, field 3=size."""
    rows: dict[str, tuple[int, int]] = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) < 4:
            raise ValueError(f"malformed result row: {raw!r}")
        name = parts[0]
        time_s = int(parts[2])
        size = int(parts[3])
        if size != 0:
            rows[name] = (time_s, size)
    return rows


def mean_reduction_pct(baseline: list[int], treatment: list[int]) -> float:
    return statistics.mean((b - t) / b * 100.0 for b, t in zip(baseline, treatment))


def aggregate_ratio(numer: list[float], denom: list[float], kind: str) -> float:
    ratios = [n / d for n, d in zip(numer, denom)]
    if kind == "geometric":
        return math.exp(statistics.mean(math.log(x) for x in ratios))
    return statistics.mean(ratios)


def close(actual: float, expected: float, tolerance: float = 0.03) -> bool:
    return abs(actual - expected) <= tolerance


def compute_language(lang: str, cfg: dict) -> dict:
    fetched = {}
    for key in ("perses", "sfc_perses", "vulcan", "sfc_vulcan"):
        fetched[key] = parse(fetch(f"{BASE}/{lang}/{cfg[key]}"))

    # The official scripts define the benchmark set from the SFC result file.
    names = list(fetched["sfc_perses"].keys())
    for key, rows in fetched.items():
        missing = [name for name in names if name not in rows]
        if missing:
            raise AssertionError(f"{lang}/{key}: {len(missing)} missing benchmark rows")

    perses_t = [fetched["perses"][n][0] for n in names]
    perses_s = [fetched["perses"][n][1] for n in names]
    vulcan_t = [fetched["vulcan"][n][0] for n in names]
    vulcan_s = [fetched["vulcan"][n][1] for n in names]
    sfc_p_t_stage = [fetched["sfc_perses"][n][0] for n in names]
    sfc_p_s = [fetched["sfc_perses"][n][1] for n in names]
    sfc_v_t_stage = [fetched["sfc_vulcan"][n][0] for n in names]
    sfc_v_s = [fetched["sfc_vulcan"][n][1] for n in names]

    if cfg["sfc_perses_time_includes_baseline"]:
        sfc_p_t = sfc_p_t_stage
    else:
        sfc_p_t = [a + b for a, b in zip(perses_t, sfc_p_t_stage)]
    sfc_v_t = [a + b for a, b in zip(vulcan_t, sfc_v_t_stage)]

    result = {
        "cases": len(names),
        "sfc_perses_reduction_pct": mean_reduction_pct(perses_s, sfc_p_s),
        "sfc_vulcan_reduction_pct": mean_reduction_pct(vulcan_s, sfc_v_s),
        "sfc_perses_time_x": aggregate_ratio(sfc_p_t, perses_t, cfg["time_aggregate"]),
        "sfc_vulcan_time_x": aggregate_ratio(sfc_v_t, vulcan_t, cfg["time_aggregate"]),
        "time_aggregate": cfg["time_aggregate"],
    }
    return result


def main() -> None:
    report = {
        "artifact_repo": ARTIFACT_REPO,
        "artifact_commit": ARTIFACT_COMMIT,
        "level": "L1-reported-results-minimization",
        "paper_abstract_conflict": {
            "sfcperses_smt_time_x_abstract": 1.42,
            "sfcperses_smt_time_x_main_text": 3.97,
            "note": "The artifact analysis convention is compared against the RQ1 main-text value.",
        },
        "languages": {},
    }

    total = 0
    for lang, cfg in LANG.items():
        result = compute_language(lang, cfg)
        expected = PAPER[lang]
        result["paper"] = expected
        result["matches"] = {
            metric: close(result[metric], expected[metric]) for metric in expected
        }
        assert result["cases"] == cfg["expected_cases"], (lang, result["cases"])
        # Size results are the central RQ1 effectiveness claims and must match.
        assert result["matches"]["sfc_perses_reduction_pct"], (lang, result)
        assert result["matches"]["sfc_vulcan_reduction_pct"], (lang, result)
        report["languages"][lang] = result
        total += result["cases"]

    report["total_minimization_cases"] = total
    assert total == 245
    report["all_headline_size_claims_match"] = all(
        data["matches"][metric]
        for data in report["languages"].values()
        for metric in ("sfc_perses_reduction_pct", "sfc_vulcan_reduction_pct")
    )
    report["all_main_text_time_claims_match"] = all(
        data["matches"][metric]
        for data in report["languages"].values()
        for metric in ("sfc_perses_time_x", "sfc_vulcan_time_x")
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "l1-minimization.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

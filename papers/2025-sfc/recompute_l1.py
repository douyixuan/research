#!/usr/bin/env python3
"""Recompute SFC's headline minimization claims from the official released CSVs.

This is L1 evidence: it reprocesses author-released outputs. It does not rerun reducers.
"""
from __future__ import annotations

import csv
import io
import json
import statistics
import urllib.request
from pathlib import Path

ARTIFACT_COMMIT = "ccf633861cdda312f5f6a6fba8a68f08cfa93888"
BASE = (
    "https://raw.githubusercontent.com/sfc-reducer/sfc-reducer/"
    f"{ARTIFACT_COMMIT}/benchmark/results_csv"
)
RESULTS = Path(__file__).resolve().parent / "results"

# Positive values mean the SFC variant is this percentage smaller than its baseline.
PAPER = {
    "c_sfc_perses": 36.82,
    "rust_sfc_perses": 18.71,
    "smt_sfc_perses": 41.05,
    "c_sfc_vulcan": 14.51,
    "rust_sfc_vulcan": 7.65,
    "smt_sfc_vulcan": 7.66,
}


def fetch_rows(language: str, filename: str) -> dict[str, dict[str, int]]:
    url = f"{BASE}/{language}/{filename}"
    with urllib.request.urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8")
    rows: dict[str, dict[str, int]] = {}
    for raw in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not raw:
            continue
        # Official plot scripts use column 2 as time and column 3 as token size.
        rows[raw[0].strip()] = {
            "time": int(raw[2].strip()),
            "size": int(raw[3].strip()),
        }
    return rows


def smaller_percent(
    baseline: dict[str, dict[str, int]],
    treatment: dict[str, dict[str, int]],
) -> tuple[float, int]:
    # Match the artifact plot scripts: the treatment file defines the benchmark set.
    names = list(treatment)
    missing = [name for name in names if name not in baseline]
    if missing:
        raise RuntimeError(f"baseline is missing {len(missing)} treatment cases: {missing[:3]}")
    changes = [
        (treatment[name]["size"] - baseline[name]["size"]) / baseline[name]["size"]
        for name in names
        if treatment[name]["size"] != 0 and baseline[name]["size"] != 0
    ]
    return -100.0 * statistics.mean(changes), len(changes)


def main() -> None:
    configs = {
        "c": {
            "perses": "perses_results.csv",
            "sfc_perses": "proj_results.csv",
            "vulcan": "vulcan_results.csv",
            "sfc_vulcan": "proj_after_vulcan_results.csv",
        },
        "rust": {
            "perses": "perses_results.csv",
            "sfc_perses": "proj_after_perses_results.csv",
            "vulcan": "vulcan_results.csv",
            "sfc_vulcan": "proj_after_vulcan_results.csv",
        },
        "smt": {
            "perses": "perses_results.csv",
            "sfc_perses": "proj_after_perses_results.csv",
            "vulcan": "vulcan_results.csv",
            "sfc_vulcan": "proj_after_vulcan_results.csv",
        },
    }

    report: dict[str, object] = {
        "artifact_commit": ARTIFACT_COMMIT,
        "reproduction_level": "scoped L1 minimization-results recomputation",
        "claims": {},
    }

    for language, filenames in configs.items():
        data = {name: fetch_rows(language, fn) for name, fn in filenames.items()}
        for baseline_name in ("perses", "vulcan"):
            treatment_name = f"sfc_{baseline_name}"
            value, count = smaller_percent(data[baseline_name], data[treatment_name])
            key = f"{language}_{treatment_name}"
            expected = PAPER[key]
            rounded = round(value + 1e-12, 2)
            status = "exact-at-2dp" if rounded == expected else "MISMATCH"
            report["claims"][key] = {
                "paper_percent_smaller": expected,
                "recomputed_percent_smaller": value,
                "recomputed_2dp": rounded,
                "cases": count,
                "status": status,
            }
            print(
                f"{key}: {value:.6f}% smaller; paper={expected:.2f}%; "
                f"n={count}; {status}"
            )
            if status != "exact-at-2dp":
                raise SystemExit(f"released-result mismatch for {key}")

    expected_counts = {"c": 20, "rust": 20, "smt": 205}
    for language, expected in expected_counts.items():
        actual = report["claims"][f"{language}_sfc_perses"]["cases"]
        if actual != expected:
            raise SystemExit(f"unexpected {language} case count: {actual}, expected {expected}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "l1-summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {RESULTS / 'l1-summary.json'}")


if __name__ == "__main__":
    main()

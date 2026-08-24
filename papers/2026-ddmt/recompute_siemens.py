#!/usr/bin/env python3
"""Recompute the released Siemens DDMT/ddmin summary rows.

This intentionally uses only the Python standard library.  The upstream files
store one record as:

    versionN
    tc:<test-case>
    data:<size>;<queries>;<seconds>;...

Table VI compares only program/input pairs for which both approaches apply, so
we join records by (faulty-version, test-case) before computing means.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


CASES = {
    "printtokens": {
        "dd": "result-summary-pt-dd.txt",
        "mr": "result-summary-pt-MR2.txt",
        "mr_name": "MR2",
        "paper": {"dd": [3.72, 30.0, 0.08], "mr": [2.43, 19.0, 1.68]},
    },
    "printtokens2": {
        "dd": "result-summary-pt2-dd.txt",
        "mr": "result-summary-pt2-MR3.txt",
        "mr_name": "MR3",
        "paper": {"dd": [1.96, 21.0, 0.06], "mr": [2.24, 22.0, 1.97]},
    },
    "schedule": {
        # The upstream artifact really spells this file "chedule".
        "dd": "result-summary-chedule-dd.txt",
        "mr": "result-summary--schedule-MR1.txt",
        "mr_name": "MR1",
        "paper": {"dd": [14.70, 221.0, 1.36], "mr": [9.30, 162.0, 13.94]},
    },
}


def parse_summary(path: Path) -> dict[tuple[str, str], tuple[float, float, float]]:
    records: dict[tuple[str, str], tuple[float, float, float]] = {}
    version: str | None = None
    tc: str | None = None
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("version"):
            version = line
            tc = None
        elif line.startswith("tc:"):
            tc = line[3:].strip()
        elif line.startswith("data:") and version and tc:
            parts = line[5:].split(";")
            if len(parts) < 3:
                continue
            try:
                metrics = (float(parts[0]), float(parts[1]), float(parts[2]))
            except ValueError:
                continue
            records[(version, tc)] = metrics
            tc = None
    return records


def means(records: dict[tuple[str, str], tuple[float, float, float]], keys: set[tuple[str, str]]) -> list[float]:
    return [statistics.fmean(records[k][i] for k in keys) for i in range(3)]


def close_enough(actual: list[float], expected: list[float]) -> tuple[bool, list[float]]:
    # Paper values are rounded to 2 decimals for size/time and to integers for
    # query count.  These tolerances are stricter than the displayed precision.
    tolerances = [0.011, 0.51, 0.011]
    errors = [abs(a - e) for a, e in zip(actual, expected)]
    return all(err <= tol for err, tol in zip(errors, tolerances)), errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("siemens_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.siemens_dir
    report: dict[str, object] = {
        "scope": "released Siemens summaries, best-MR rows available in artifact",
        "subjects": {},
        "artifact_gaps": [],
    }
    failures: list[str] = []

    replace_mr3 = root / "result-summary--replace-MR3.txt"
    if not replace_mr3.exists():
        report["artifact_gaps"].append(
            "Paper Table V identifies replace/MR3 as best MR, but result-summary--replace-MR3.txt is absent."
        )

    for subject, cfg in CASES.items():
        dd_path = root / str(cfg["dd"])
        mr_path = root / str(cfg["mr"])
        if not dd_path.exists() or not mr_path.exists():
            failures.append(f"{subject}: missing expected released summary file")
            continue

        dd = parse_summary(dd_path)
        mr = parse_summary(mr_path)
        common = set(dd) & set(mr)
        if not common:
            failures.append(f"{subject}: no common (version,test-case) records")
            continue

        dd_mean = means(dd, common)
        mr_mean = means(mr, common)
        dd_ok, dd_err = close_enough(dd_mean, cfg["paper"]["dd"])
        mr_ok, mr_err = close_enough(mr_mean, cfg["paper"]["mr"])
        if not dd_ok:
            failures.append(f"{subject}: ddmin means differ from Table VI: {dd_mean}")
        if not mr_ok:
            failures.append(f"{subject}: DDMT means differ from Table VI: {mr_mean}")

        report["subjects"][subject] = {
            "best_mr": cfg["mr_name"],
            "matched_pairs": len(common),
            "released_records": {"ddmin": len(dd), "ddmt": len(mr)},
            "recomputed": {
                "ddmin": {"size": dd_mean[0], "queries": dd_mean[1], "seconds": dd_mean[2]},
                "ddmt": {"size": mr_mean[0], "queries": mr_mean[1], "seconds": mr_mean[2]},
            },
            "paper": {
                "ddmin": {"size": cfg["paper"]["dd"][0], "queries": cfg["paper"]["dd"][1], "seconds": cfg["paper"]["dd"][2]},
                "ddmt": {"size": cfg["paper"]["mr"][0], "queries": cfg["paper"]["mr"][1], "seconds": cfg["paper"]["mr"][2]},
            },
            "absolute_error": {"ddmin": dd_err, "ddmt": mr_err},
            "matches_displayed_table": dd_ok and mr_ok,
        }

    report["status"] = "pass" if not failures else "fail"
    report["failures"] = failures
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

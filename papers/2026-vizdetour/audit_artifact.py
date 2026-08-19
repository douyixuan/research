#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PAPER_TABLE = {
    "matplotlib": {"reported": 20, "confirmed": 20, "pending_fix": 8, "fixed": 11},
    "bokeh": {"reported": 18, "confirmed": 13, "pending_fix": 4, "fixed": 7},
    "plotly": {"reported": 9, "confirmed": 6, "pending_fix": 2, "fixed": 0},
}


def yes(value: str) -> bool:
    return value.strip().lower().startswith("yes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/artifact-audit.json"),
    )
    args = parser.parse_args()

    with args.csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["Library"].strip().lower()].append(row)

    observed = {}
    symptom_counts = Counter()
    component_counts = Counter()
    mutation_counts = Counter()

    for library in PAPER_TABLE:
        library_rows = grouped[library]
        # The released CSV includes rejected reports (Confirmed=No) and a few
        # non-new reports (New=No). Table I's "reported new bugs" excludes both.
        paper_population = [
            row
            for row in library_rows
            if row["Confirmed"].strip() != "No" and row["New"].strip() != "No"
        ]
        confirmed_rows = [row for row in paper_population if yes(row["Confirmed"])]
        fixed_rows = [row for row in confirmed_rows if yes(row["Fixed"])]
        pending_fix_rows = [
            row
            for row in confirmed_rows
            if yes(row["PR"]) and not yes(row["Fixed"])
        ]

        observed[library] = {
            "csv_rows": len(library_rows),
            "reported": len(paper_population),
            "confirmed": len(confirmed_rows),
            "pending_fix": len(pending_fix_rows),
            "fixed": len(fixed_rows),
        }

        for row in confirmed_rows:
            if row["Symptom"] not in ("", "-"):
                symptom_counts[row["Symptom"]] += 1
            if row["Buggy Component"] not in ("", "-"):
                component_counts[row["Buggy Component"]] += 1
            if row["Mutation"] not in ("", "-"):
                mutation_counts[row["Mutation"]] += 1

    totals = {
        key: sum(observed[lib][key] for lib in PAPER_TABLE)
        for key in ("reported", "confirmed", "pending_fix", "fixed")
    }
    expected_totals = {
        key: sum(PAPER_TABLE[lib][key] for lib in PAPER_TABLE)
        for key in ("reported", "confirmed", "pending_fix", "fixed")
    }

    report = {
        "paper_table": PAPER_TABLE,
        "observed_from_released_csv": observed,
        "paper_totals": expected_totals,
        "observed_totals": totals,
        "confirmed_bug_breakdown": {
            "symptom": dict(symptom_counts),
            "component": dict(component_counts),
            "mutation": dict(mutation_counts),
        },
        "notes": [
            "reported/confirmed/fixed are treated as stable paper claims and asserted",
            "pending-fix is intentionally not asserted because PR/fix lifecycle fields can drift after publication",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))

    for key in ("reported", "confirmed", "fixed"):
        if totals[key] != expected_totals[key]:
            raise SystemExit(
                f"Released artifact no longer reconstructs paper total {key}: "
                f"observed={totals[key]}, expected={expected_totals[key]}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

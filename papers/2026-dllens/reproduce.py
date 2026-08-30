#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

PIN = "0f617e92c34d60bfdd3bc06d80c17d938879ed9c"
EXPECTED_ROUNDS = {
    "tensorflow": [604, 37, 17, 14, 17],
    "pytorch": [608, 47, 34, 12, 11],
}
TENSORSCOPE = {"tensorflow": 304, "pytorch": 458}
EXPECTED_BUGS = {
    "tensorflow": 37,
    "pytorch": 22,
    "confirmed": 59,
    "unknown": 46,
    "known": 13,
    "fixed_unknown": 10,
}


def nonempty_lines(path: Path) -> int:
    return sum(1 for line in path.read_text().splitlines() if line.strip())


def bug_table(path: Path) -> dict[str, int]:
    counts = {"total": 0, "unknown": 0, "known": 0, "fixed_unknown": 0}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["Link"].strip() == "Total Bug":
                continue
            count = int(row["Bug Count"])
            status = row["Status"].strip()
            counts["total"] += count
            if status in {"Fixed", "Previously Unknown"}:
                counts["unknown"] += count
                if status == "Fixed":
                    counts["fixed_unknown"] += count
            elif status in {"Known", "Known Bug", "Already Fixed"}:
                counts["known"] += count
            else:
                raise AssertionError(f"Unhandled bug status {status!r} in {path}")
    return counts


def git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact", type=Path)
    ap.add_argument("--output", type=Path, default=Path("papers/2026-dllens/results"))
    args = ap.parse_args()
    root = args.artifact.resolve()

    required = [
        "README.md",
        "RQ1CounterpartSynthesisEvaluation.ipynb",
        "RQ2ConstraintExtraction.ipynb",
        "RQ3Coverage.ipynb",
        "tensorflow_confirmed_bugs.csv",
        "pytorch_confirmed_bugs.csv",
        "scripts/synthesize_counterpart.py",
        "scripts/extract_constraint.py",
        "scripts/gen_tests.py",
        "codes/counterpart/counterpart_agent.py",
        "codes/prompt_text/counterpart_collection_prefix.py",
        "codes/prompt_text/condition_solver_template.py",
    ]
    missing = [p for p in required if not (root / p).exists()]
    if missing:
        raise AssertionError(f"Missing expected artifact paths: {missing}")

    head = git_head(root)
    if head is not None and head != PIN:
        raise AssertionError(f"Artifact drift: expected {PIN}, got {head}")

    rounds: dict[str, list[int]] = {}
    totals: dict[str, int] = {}
    for lib in ("tensorflow", "pytorch"):
        base = root / "data" / "working_dir" / "rq1" / "dllens" / lib
        rounds[lib] = [nonempty_lines(base / f"round{i}.txt") for i in range(1, 6)]
        totals[lib] = sum(rounds[lib])
        assert rounds[lib] == EXPECTED_ROUNDS[lib], (lib, rounds[lib])

    tf_improvement = (totals["tensorflow"] / TENSORSCOPE["tensorflow"] - 1) * 100
    torch_improvement = (totals["pytorch"] / TENSORSCOPE["pytorch"] - 1) * 100
    combined_ratio = sum(totals.values()) / sum(TENSORSCOPE.values())

    assert round(tf_improvement, 2) == 126.64
    assert round(torch_improvement, 2) == 55.46
    assert round(combined_ratio, 2) == 1.84

    tf_bugs = bug_table(root / "tensorflow_confirmed_bugs.csv")
    torch_bugs = bug_table(root / "pytorch_confirmed_bugs.csv")
    bug_summary = {
        "tensorflow": tf_bugs["total"],
        "pytorch": torch_bugs["total"],
        "confirmed": tf_bugs["total"] + torch_bugs["total"],
        "unknown": tf_bugs["unknown"] + torch_bugs["unknown"],
        "known": tf_bugs["known"] + torch_bugs["known"],
        "fixed_unknown": tf_bugs["fixed_unknown"] + torch_bugs["fixed_unknown"],
    }
    assert bug_summary == EXPECTED_BUGS, bug_summary

    report = {
        "artifact_repo": "maybeLee/DLLens",
        "artifact_commit": PIN,
        "reproduction_level": "L1 partial + L0 implementation audit",
        "rq1": {
            "round_counts": rounds,
            "dllens_totals": totals,
            "tensorscope_paper_baseline": TENSORSCOPE,
            "tensorflow_improvement_percent": round(tf_improvement, 2),
            "pytorch_improvement_percent": round(torch_improvement, 2),
            "combined_ratio": round(combined_ratio, 2),
        },
        "rq4_confirmed_bugs": bug_summary,
        "not_reproduced": {
            "all_detected_bugs": 71,
            "branch_coverage_improvement_percent": 7.23,
            "bug_detection_ratio_on_200_apis": 1.88,
            "reason": "This deterministic lane reprocesses released RQ1/RQ4 raw data; it does not rerun LLM synthesis, framework execution, RQ3 coverage, or manual bug triage.",
        },
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "dllens-report.json").write_text(json.dumps(report, indent=2) + "\n")
    md = f"""# DLLens reproduction report\n\n- Level: **{report['reproduction_level']}**\n- Artifact commit: `{PIN}`\n- RQ1 TensorFlow: `{rounds['tensorflow']}` → **{totals['tensorflow']}** counterparts\n- RQ1 PyTorch: `{rounds['pytorch']}` → **{totals['pytorch']}** counterparts\n- Combined DLLens/TensorScope ratio: **{combined_ratio:.2f}×**\n- Confirmed bugs: **{bug_summary['confirmed']}** = {bug_summary['unknown']} previously unknown + {bug_summary['known']} known\n- Previously unknown and later fixed: **{bug_summary['fixed_unknown']}**\n\nThis is not L2/L3: no fresh LLM generation or DL-library campaign was executed.\n"""
    (args.output / "SUMMARY.md").write_text(md)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

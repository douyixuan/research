#!/usr/bin/env python3
"""Reprocess the pinned OPERA artifact's published APFD data and bug ledger."""
from __future__ import annotations

import ast
import json
import re
import urllib.request
from pathlib import Path

UPSTREAM_COMMIT = "926ea4315c86c35dcfdcd80a2c6b2a7ac9c07cf7"
RAW = f"https://raw.githubusercontent.com/ShenQingchao/OPERA/{UPSTREAM_COMMIT}"
SUBJECTS = {
    "tvm": ["torch", "keras", "onnx"],
    "trt": ["torch", "onnx"],
    "ov": ["torch", "keras", "onnx"],
}
TEST_NUM = {"torch": 97134, "keras": 62976, "onnx": 1013}
STRATEGIES = ["our", "random", "fast", "cov", "delta_cov"]
PAPER = {
    "mean_apfd_our": 0.898,
    "improvement_random_pct": 13.1,
    "improvement_fast_pct": 11.9,
    "improvement_cov_pct": 47.4,
    "improvement_delta_cov_pct": 37.2,
    "confirmed_or_fixed_at_paper": 90,
    "total_bugs": 170,
}


def fetch_text(path: str) -> str:
    with urllib.request.urlopen(f"{RAW}/{path}", timeout=60) as response:
        return response.read().decode("utf-8")


def artifact_dicts(source: str):
    tree = ast.parse(source)
    wanted = {"all_tvm_tcp_res", "all_trt_tcp_res", "all_ov_tcp_res"}
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in wanted:
                out[name] = ast.literal_eval(node.value)
    missing = wanted - out.keys()
    if missing:
        raise RuntimeError(f"missing artifact dictionaries: {sorted(missing)}")
    return out


def apfd(test_num: int, bug_ranks: list[int]) -> float:
    return 1 - sum(bug_ranks) / (len(bug_ranks) * test_num) + 1 / (2 * test_num)


def key(project: str, strategy: str) -> str:
    return f"{project}_{strategy}"


def reprocess_apfd(dicts):
    by_subject = {}
    by_strategy = {s: [] for s in STRATEGIES}
    for sut, projects in SUBJECTS.items():
        data = dicts[f"all_{sut}_tcp_res"]
        for project in projects:
            subject = f"{sut}-{project}"
            by_subject[subject] = {}
            for strategy in STRATEGIES:
                ranks = data[key(project, strategy)]
                value = apfd(TEST_NUM[project], ranks)
                by_subject[subject][strategy] = value
                by_strategy[strategy].append(value)
    means = {s: sum(v) / len(v) for s, v in by_strategy.items()}
    improvements = {
        s: (means["our"] - means[s]) / means[s] * 100
        for s in STRATEGIES if s != "our"
    }
    return by_subject, means, improvements


def parse_bug_ledger(markdown: str) -> int:
    total = 0
    for line in markdown.splitlines():
        if not line.startswith("|") or "#Bugs" in line or "---" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"\d+", cells[1]):
            total += int(cells[1])
    return total


def close(actual: float, expected: float, tol: float, label: str):
    if abs(actual - expected) > tol:
        raise AssertionError(f"{label}: actual={actual:.6f} expected={expected:.6f} tol={tol}")


def main():
    source = fetch_text("analyze_results/cal_APFD_all.py")
    bug_md = fetch_text("bugs.md")
    dicts = artifact_dicts(source)
    by_subject, means, improvements = reprocess_apfd(dicts)
    ledger_total = parse_bug_ledger(bug_md)

    close(means["our"], PAPER["mean_apfd_our"], 0.0015, "mean APFD")
    close(improvements["random"], PAPER["improvement_random_pct"], 0.25, "vs random")
    close(improvements["fast"], PAPER["improvement_fast_pct"], 0.25, "vs FAST")
    close(improvements["cov"], PAPER["improvement_cov_pct"], 0.25, "vs total coverage")
    close(improvements["delta_cov"], PAPER["improvement_delta_cov_pct"], 0.25, "vs additional coverage")
    if ledger_total != 102:
        raise AssertionError(f"artifact bug ledger count drifted: expected 102 at pinned commit, got {ledger_total}")

    result = {
        "reproduction_level": "L1 reported-results (APFD) + L0 artifact audit",
        "upstream_commit": UPSTREAM_COMMIT,
        "subjects": by_subject,
        "mean_apfd": means,
        "improvement_pct": improvements,
        "paper_claims": PAPER,
        "artifact_confirmed_or_fixed_ledger": ledger_total,
        "artifact_drift": {
            "paper_confirmed_or_fixed": 90,
            "pinned_artifact_ledger": ledger_total,
            "interpretation": "post-paper bug status update; not a mismatch in the original 170-bug total"
        },
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/l1.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

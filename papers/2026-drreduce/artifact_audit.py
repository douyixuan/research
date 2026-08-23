#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

RATIO_RE = re.compile(r"Reduction ratio is\s+(\d+)/(\d+)=")
TIME_RE = re.compile(r"Elapsed time is\s+(\d+)\s+seconds")
QUERY_RE = re.compile(r"Test script execution count:\s+(\d+)")
PAPER_NEW_JDK = ["JDK-8271954", "JDK-8272562", "JDK-8293941", "JDK-8331717"]


def parse_result(path: Path):
    text = path.read_text(errors="replace")
    ratio = RATIO_RE.search(text)
    if not ratio:
        return None
    time = TIME_RE.search(text)
    queries = QUERY_RE.search(text)
    return {
        "final_tokens": int(ratio.group(1)),
        "input_tokens": int(ratio.group(2)),
        "elapsed_seconds": int(time.group(1)) if time else None,
        "queries": int(queries.group(1)) if queries else None,
        "path": str(path),
    }


def first_existing(base: Path, candidates):
    for rel in candidates:
        p = base / rel
        if p.is_file():
            parsed = parse_result(p)
            if parsed:
                return parsed
    return None


def find_result_by_token(base: Path, token_count: int, must_contain=()):
    matches = []
    for p in base.rglob("*.txt"):
        lower = str(p).lower()
        if any(term.lower() not in lower for term in must_contain):
            continue
        parsed = parse_result(p)
        if parsed and parsed["final_tokens"] == token_count:
            matches.append(parsed)
    return matches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact", type=Path)
    ap.add_argument("--out", type=Path, default=Path("results/artifact-audit.json"))
    args = ap.parse_args()
    root = args.artifact.resolve()

    counts = {}
    bug_names = []
    family_names = {}
    for family in ("clang", "gcc", "java"):
        d = root / family
        names = sorted(p.name for p in d.iterdir() if p.is_dir())
        family_names[family] = names
        counts[family] = len(names)
        bug_names.extend(f"{family}/{n}" for n in names)

    released_total = sum(counts.values())
    # Paper Table 3 says 28 = 16 C + 12 Java, including four newly collected
    # JDK bugs. The pinned public data commit contains all 16 C cases but only
    # eight Java cases, i.e. 24 total. Treat this as a reproducibility gap rather
    # than pretending the release is complete.
    if counts != {"clang": 6, "gcc": 10, "java": 8}:
        raise SystemExit(f"unexpected released corpus shape: {counts}")
    missing_new_jdk = [name for name in PAPER_NEW_JDK if name not in family_names["java"]]
    if missing_new_jdk != PAPER_NEW_JDK:
        raise SystemExit(f"unexpected new-JDK availability: missing={missing_new_jdk}")

    case = root / "gcc" / "gcc-65383"
    paper_perses = first_existing(case, [
        "perses_result_2018/perses_times.txt",
        "perses_result_2018/perses_result.txt",
    ])
    paper_wdd = first_existing(case, [
        "wprobdd_result.txt/wprobdd_result.txt",
        "wprobdd_result/wprobdd_result.txt",
    ])
    paper_drreduce = first_existing(case, [
        "ssreducer/perses_result_2018/perses_result.txt",
        "ssreducer/perses_result_2018/perses_times.txt",
    ])

    required = {
        "perses": (paper_perses, 384),
        "wdd": (paper_wdd, 144),
        "drreduce": (paper_drreduce, 122),
    }
    for name, (record, expected) in required.items():
        if not record:
            raise SystemExit(f"missing gcc-65383 {name} paper-era result")
        if record["final_tokens"] != expected:
            raise SystemExit(
                f"gcc-65383 {name}: expected {expected} tokens, got {record['final_tokens']}"
            )

    cdd_candidates = find_result_by_token(case, 156, must_contain=("cdd",))

    # The artifact also contains a non-2018 Perses lane. It is not the paper baseline,
    # but recording it makes baseline/toolchain drift explicit rather than silently
    # mixing snapshots.
    alternate_perses = first_existing(case, ["perses_result/perses_times.txt"])
    alternate_drreduce = first_existing(case, [
        "ssreducer/perses_result/perses_times.txt",
        "ssreducer/perses_result/perses_result.txt",
    ])

    summary = {
        "artifact": {
            "root": str(root),
            "paper_expected_programs": 28,
            "released_evaluation_programs": released_total,
            "counts": counts,
            "programs": bug_names,
            "missing_paper_programs": [f"java/{name}" for name in missing_new_jdk],
            "coverage_note": (
                "Paper Table 3 has 12 Java cases; pinned public data has 8. "
                "The four newly collected JDK cases are absent from java/."
            ),
        },
        "gcc-65383-paper-era": {
            "perses": paper_perses,
            "wdd": paper_wdd,
            "cdd_candidates": cdd_candidates,
            "drreduce": paper_drreduce,
            "paper_claim_tokens": {"perses": 384, "wdd": 144, "cdd": 156, "drreduce": 122},
        },
        "gcc-65383-alternate-artifact-lane": {
            "perses": alternate_perses,
            "drreduce": alternate_drreduce,
            "warning": "These are artifact-side alternate runs, not the paper-era baseline.",
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

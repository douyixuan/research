#!/usr/bin/env python3
import argparse
import json
import statistics
import subprocess
from pathlib import Path

PAPER_CLAIMS = {"c": 24.93, "rust": 4.47, "js": 11.71}
EXPECTED_CASES = {"c": 20, "rust": 20, "js": 10}
PROGRAM_NAMES = {"c": "small.c", "rust": "small.rs", "js": "small.js"}
UPSTREAM_COMMIT = "d45ea0e261a8f4c7ec05fc29ccb5aadd19d673cc"


def count_tokens(jar: Path, program: Path) -> int:
    proc = subprocess.run(
        ["java", "-jar", str(jar), "--", str(program)],
        check=True,
        text=True,
        capture_output=True,
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"token counter produced no output for {program}")
    return int(lines[-1])


def case_dirs(path: Path):
    return {p.name: p for p in path.iterdir() if p.is_dir()}


def compute_language(artifact: Path, lang: str):
    suite = artifact / "benchmark_suites" / lang
    vulcan = case_dirs(suite / "vulcan")
    lpr_runs = [case_dirs(suite / f"lpr_{i}") for i in range(5)]
    common = sorted(set(vulcan).intersection(*(set(run) for run in lpr_runs)))
    if len(common) != EXPECTED_CASES[lang]:
        raise RuntimeError(
            f"{lang}: expected {EXPECTED_CASES[lang]} common cases, found {len(common)}"
        )

    jar = artifact / "tools" / "token_counter_deploy.jar"
    program = PROGRAM_NAMES[lang]
    rows = []
    for case in common:
        v = count_tokens(jar, vulcan[case] / program)
        lprs = [count_tokens(jar, run[case] / program) for run in lpr_runs]
        lpr_mean = statistics.mean(lprs)
        rows.append(
            {
                "case": case,
                "vulcan_tokens": v,
                "lpr_tokens": lprs,
                "lpr_mean_tokens": lpr_mean,
                "improvement_pct": (v - lpr_mean) / v * 100.0,
            }
        )

    mean_case = statistics.mean(r["improvement_pct"] for r in rows)
    total_v = sum(r["vulcan_tokens"] for r in rows)
    total_lpr = sum(r["lpr_mean_tokens"] for r in rows)
    ratio_of_totals = (total_v - total_lpr) / total_v * 100.0
    pairwise = statistics.mean(
        (r["vulcan_tokens"] - lpr) / r["vulcan_tokens"] * 100.0
        for r in rows
        for lpr in r["lpr_tokens"]
    )
    claim = PAPER_CLAIMS[lang]
    return {
        "language": lang,
        "cases": len(rows),
        "runs_per_case": 5,
        "paper_effectiveness_claim_pct": claim,
        "mean_case_improvement_pct": mean_case,
        "mean_pairwise_improvement_pct": pairwise,
        "ratio_of_totals_improvement_pct": ratio_of_totals,
        "delta_to_paper_mean_case_pp": mean_case - claim,
        "delta_to_paper_ratio_of_totals_pp": ratio_of_totals - claim,
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    artifact = args.artifact.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    sha = subprocess.check_output(
        ["git", "-C", str(artifact), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != UPSTREAM_COMMIT:
        raise RuntimeError(f"expected upstream {UPSTREAM_COMMIT}, got {sha}")

    results = {
        "upstream": "zhangxiaosa/LPR",
        "upstream_commit": sha,
        "level": "L1-partial",
        "note": (
            "Reprocesses author-released reduced programs. It does not rerun the LLM/reducer pipeline. "
            "The artifact README also states that some precomputed reruns differ from the original paper runs."
        ),
        "languages": {},
    }
    for lang in ("c", "rust", "js"):
        results["languages"][lang] = compute_language(artifact, lang)

    (output / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    md = [
        "# LPR artifact reprocessing result",
        "",
        f"Pinned upstream: `{sha}`",
        "",
        "| Language | Cases | Paper claim | Mean per-case recompute | Ratio-of-totals recompute | Delta (mean-case) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for lang in ("c", "rust", "js"):
        r = results["languages"][lang]
        md.append(
            f"| {lang} | {r['cases']} | {r['paper_effectiveness_claim_pct']:.2f}% | "
            f"{r['mean_case_improvement_pct']:.4f}% | {r['ratio_of_totals_improvement_pct']:.4f}% | "
            f"{r['delta_to_paper_mean_case_pp']:+.4f} pp |"
        )
    md.extend(
        [
            "",
            "This is **L1 partial** evidence only: released outputs are re-counted with the authors' token-counter JAR; no new LLM calls are made.",
        ]
    )
    (output / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

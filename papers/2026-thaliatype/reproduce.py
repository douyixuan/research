#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: reproduce.py <path-to-thalia-type-artifact>")

upstream = Path(sys.argv[1]).resolve()
os.chdir(upstream)
sys.path.insert(0, str(upstream))

from compare_results import process_files_precision_recall  # noqa: E402

EXPECTED = {
    "StatType-SO": {
        "snr": (95.50, 91.46, 93.44),
        "llama3.1-8b": (76.92, 69.46, 73.00),
        "llama3.1-70b": (86.08, 83.69, 84.87),
        "gpt-4o-mini": (86.34, 89.92, 88.09),
        "gpt-4o": (95.66, 95.00, 95.33),
    },
    "ThaliaType": {
        "snr": (84.15, 84.43, 84.29),
        "llama3.1-8b": (31.27, 19.40, 23.95),
        "llama3.1-70b": (61.58, 25.85, 36.41),
        "gpt-4o-mini": (66.64, 37.73, 48.18),
        "gpt-4o": (54.74, 44.54, 49.12),
    },
}

SPECS = {
    "StatType-SO": (Path("snippets/so"), Path("outputs"), "so"),
    "ThaliaType": (Path("snippets-thalia/thalia-cs"), Path("outputs-thalia"), "thalia-cs"),
}


def pct_tuple(correct: int, recommended: int, expected: int):
    precision = correct / recommended if recommended else 1.0
    recall = correct / expected if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return tuple(round(v * 100, 2) for v in (precision, recall, f1))


report = {
    "upstream_commit": "08895f35945ac84e78b91db9f908f401246e3c15",
    "level": "L1-partial",
    "results": {},
    "artifact_gaps": [],
}

for benchmark, (input_dir, output_root, suffix) in SPECS.items():
    report["results"][benchmark] = {}
    for model, expected_metrics in EXPECTED[benchmark].items():
        output_dir = output_root / f"{model}-output-{suffix}"
        if not output_dir.is_dir():
            raise AssertionError(f"missing released output directory: {output_dir}")

        # The upstream implementation computes the same global P/R/F1 reported in Fig. 7.
        old_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, "w")
            correct, recommended, expected, *_ = process_files_precision_recall(
                str(input_dir), str(output_dir)
            )
        finally:
            sys.stdout.close()
            sys.stdout = old_stdout

        actual = pct_tuple(correct, recommended, expected)
        report["results"][benchmark][model] = {
            "correct": correct,
            "recommended": recommended,
            "expected": expected,
            "precision_recall_f1": actual,
            "paper_precision_recall_f1": expected_metrics,
        }
        if actual != expected_metrics:
            raise AssertionError(
                f"{benchmark}/{model}: artifact {actual} != paper {expected_metrics}"
            )
        print(f"PASS {benchmark:11s} {model:13s} P/R/F1={actual}")

for output_root in (Path("outputs"), Path("outputs-thalia")):
    starcoder = sorted(p.name for p in output_root.iterdir() if "starcoder" in p.name.lower())
    if not starcoder:
        report["artifact_gaps"].append(
            f"No StarCoder2 released result directory under {output_root}; Fig. 7 StarCoder2 cannot be recomputed from this snapshot."
        )

out = Path(os.environ.get("THALIATYPE_REPORT", "thaliatype-report.json"))
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n")
print(f"wrote {out}")
print(f"verified {sum(len(v) for v in EXPECTED.values())} paper/model benchmark cells")
print(f"artifact gaps: {len(report['artifact_gaps'])}")
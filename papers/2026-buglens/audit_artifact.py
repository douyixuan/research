#!/usr/bin/env python3
import argparse
import ast
import json
from pathlib import Path

PAPER_V3_DATASETS = {
    "gcc430": {"programs": 1235, "bugs": 29, "label": "GCC-4.3.0"},
    "gcc440": {"programs": 647, "bugs": 11, "label": "GCC-4.4.0"},
    "gcc450": {"programs": 26, "bugs": 7, "label": "GCC-4.5.0"},
    "llvm280": {"programs": 80, "bugs": 5, "label": "LLVM-2.8.0"},
    "gcc131": {"programs": 42, "bugs": 7, "label": "GCC-13.1.0"},
}


def extract_dataset_keys(evaluate_py: Path) -> set[str]:
    tree = ast.parse(evaluate_py.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "datasets":
                    value = ast.literal_eval(node.value)
                    return set(value.keys())
    raise RuntimeError("could not find literal datasets mapping in evaluate.py")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    keys = extract_dataset_keys(args.artifact / "evaluate.py")
    expected = set(PAPER_V3_DATASETS)
    missing = sorted(expected - keys)
    extra = sorted(keys - expected)

    report = {
        "paper_v3_dataset_count": len(expected),
        "artifact_evaluate_dataset_count": len(keys),
        "artifact_dataset_keys": sorted(keys),
        "missing_from_artifact_evaluate": missing,
        "extra_in_artifact_evaluate": extra,
        "paper_v3_datasets": PAPER_V3_DATASETS,
        "full_v3_reproduction_possible_from_this_artifact": not missing,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    # This is an expected audit finding, not a CI failure. CI should fail only
    # if the pinned artifact unexpectedly stops exposing the four known sets.
    required_legacy = {"gcc430", "gcc440", "gcc450", "llvm280"}
    if not required_legacy.issubset(keys):
        raise SystemExit("pinned artifact is missing one of the four released legacy datasets")


if __name__ == "__main__":
    main()

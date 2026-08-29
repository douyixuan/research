#!/usr/bin/env python3
"""Audit the pinned public source tree that matches TemplateFuzz's interface."""
import argparse
import json
from pathlib import Path

EXPECTED_DIRS = ["core", "detectors", "evaluate", "maskers", "mutators"]
EXPECTED_README_TERMS = ["M1", "M2", "M3", "M4", "M5", "bandit", "seed pool", "baseline"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    missing_dirs = [d for d in EXPECTED_DIRS if not (args.source / d).is_dir()]
    readme = (args.source / "README.md").read_text(encoding="utf-8")
    missing_terms = [term for term in EXPECTED_README_TERMS if term.lower() not in readme.lower()]
    py_files = sorted(args.source.rglob("*.py"))
    py_lines = sum(len(p.read_text(encoding="utf-8", errors="replace").splitlines()) for p in py_files)

    assert not missing_dirs, f"missing dirs: {missing_dirs}"
    assert not missing_terms, f"missing README terms: {missing_terms}"
    assert (args.source / "main.py").is_file()
    assert py_files

    result = {
        "scope": "matching public source interface audit; provenance not equated with paper-declared anonymous artifact",
        "repository": "https://github.com/FFchopon/TemplateFuzz-LLM",
        "commit": args.commit,
        "expected_dirs": EXPECTED_DIRS,
        "python_files": len(py_files),
        "python_lines": py_lines,
        "readme_terms_verified": EXPECTED_README_TERMS,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

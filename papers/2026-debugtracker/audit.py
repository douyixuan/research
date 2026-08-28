#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def fail(msg: str) -> None:
    raise SystemExit(msg)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: audit.py <DebugTracker checkout>")

    root = Path(sys.argv[1])
    test_source = (root / "src/test/runTests.ts").read_text(encoding="utf-8")
    practice = (root / "PRACTICE_TEST_REPORT.md").read_text(encoding="utf-8")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))

    run_body_match = re.search(r"function run\(\): void \{(?P<body>.*?)\n\}", test_source, re.S)
    if not run_body_match:
        fail("could not locate run() in src/test/runTests.ts")
    run_body = run_body_match.group("body")
    automated_calls = re.findall(r"^\s*(test[A-Za-z0-9_]+)\(\);\s*$", run_body, re.M)

    manual_case_ids = re.findall(r"^\|\s*(TC-[0-9]+(?:A)?)\s*\|", practice, re.M)
    manual_case_ids = list(dict.fromkeys(manual_case_ids))

    expected_automated = 16
    expected_manual = 11
    if len(automated_calls) != expected_automated:
        fail(f"automated check count drift: expected {expected_automated}, found {len(automated_calls)}")
    if len(manual_case_ids) != expected_manual:
        fail(f"manual matrix count drift: expected {expected_manual}, found {len(manual_case_ids)}")

    report = {
        "artifact_version": package.get("version"),
        "vscode_engine": package.get("engines", {}).get("vscode"),
        "automated_check_count": len(automated_calls),
        "automated_checks": automated_calls,
        "manual_trial_count": len(manual_case_ids),
        "manual_trial_ids": manual_case_ids,
        "paper_claim_match": {
            "automated_checks_16": len(automated_calls) == expected_automated,
            "manual_trials_11": len(manual_case_ids) == expected_manual,
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

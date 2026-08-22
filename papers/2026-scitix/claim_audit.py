#!/usr/bin/env python3
"""Audit claim drift between the 2025 thesis chapter and the ISSTA 2026 abstract."""

from __future__ import annotations

import json
from pathlib import Path

THESIS = {
    "snapshot": "Yiwen Dong PhD thesis, 2025, Chapter 5",
    "stack_overflow_f1": 96.6,
    "thaliatype_f1": 88.7,
    "snr_error_reduction_stack": 79.0,
    "snr_error_reduction_thalia": 37.0,
    "llm_error_reduction_max": 78.0,
}

ISSTA = {
    "snapshot": "ISSTA 2026 Researchr abstract, checked 2026-08-22",
    "stack_overflow_f1": 94.8,
    "thaliatype_f1": 86.8,
    "snr_error_reduction_stack": 77.0,
    "snr_error_reduction_thalia": 45.0,
    "llm_error_reduction_max": 78.0,
}


def main() -> None:
    metrics = [k for k in THESIS if k != "snapshot"]
    delta = {k: round(ISSTA[k] - THESIS[k], 1) for k in metrics}
    report = {
        "thesis": THESIS,
        "issta_2026": ISSTA,
        "delta_percentage_points_issta_minus_thesis": delta,
        "interpretation": (
            "The accepted ISSTA abstract reports revised headline numbers. "
            "Reproductions must pin the exact paper/artifact snapshot instead of mixing "
            "the earlier thesis chapter with the camera-ready claims."
        ),
    }
    out = Path("results/claim_drift.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

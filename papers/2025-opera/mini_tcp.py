#!/usr/bin/env python3
"""Scoped L2 mechanism reproduction of OPERA's two-dimensional prioritization.

This is intentionally a small, fresh experiment, not the official paper-scale run.
It implements the mechanism described in the paper: operator-signature gap ×
parameter-subspace novelty, with novelty updated after each selection.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Case:
    name: str
    op: str
    params: tuple[tuple[str, str], ...]
    fault: str | None = None


CASES = [
    Case("conv-default", "Conv2DTranspose", (("padding", "zero"), ("output_padding", "none"))),
    Case("conv-output-pad", "Conv2DTranspose", (("padding", "zero"), ("output_padding", "positive")), "F-output-padding"),
    Case("reshape-neg1", "Reshape", (("dim", "-1"),), "F-neg-dim"),
    Case("reshape-pos", "Reshape", (("dim", ">=2"),)),
    Case("relu-basic", "ReLU", (("inplace", "false"),)),
    Case("pad-negative", "Pad", (("padding", "negative"),), "F-negative-pad"),
]

# Library-side tests emphasize Conv2DTranspose / Reshape; compiler suite is sparse there.
DLL_COUNTS = Counter({"Conv2DTranspose": 8, "Reshape": 6, "ReLU": 2, "Pad": 4})
DLC_COUNTS = Counter({"Conv2DTranspose": 1, "Reshape": 1, "ReLU": 4, "Pad": 1})


def signature_score(op: str) -> float:
    return DLL_COUNTS[op] / DLC_COUNTS[op]


def novelty(case: Case, seen: dict[str, set[tuple[str, str]]]) -> float:
    items = set(case.params)
    if not items:
        return 0.0
    return sum(item not in seen[case.op] for item in items) / len(items)


def prioritize(cases: list[Case]) -> list[Case]:
    remaining = list(cases)
    seen: dict[str, set[tuple[str, str]]] = defaultdict(set)
    ordered = []
    while remaining:
        scored = [
            (signature_score(c.op) * novelty(c, seen), signature_score(c.op), c.name, c)
            for c in remaining
        ]
        _, _, _, chosen = max(scored, key=lambda x: (x[0], x[1], x[2]))
        ordered.append(chosen)
        seen[chosen.op].update(chosen.params)
        remaining.remove(chosen)
    return ordered


def apfd(order: list[Case]) -> float:
    fault_positions = [i + 1 for i, c in enumerate(order) if c.fault]
    n = len(order)
    m = len(fault_positions)
    return 1 - sum(fault_positions) / (n * m) + 1 / (2 * n)


def main():
    opera = prioritize(CASES)
    baseline = sorted(CASES, key=lambda c: c.name)
    opera_apfd = apfd(opera)
    baseline_apfd = apfd(baseline)
    result = {
        "reproduction_level": "scoped L2 mechanism",
        "opera_order": [c.name for c in opera],
        "baseline_order": [c.name for c in baseline],
        "opera_apfd": opera_apfd,
        "alphabetical_baseline_apfd": baseline_apfd,
        "delta_apfd": opera_apfd - baseline_apfd,
        "note": "synthetic operator instances; validates control logic only, not paper-scale bug-finding effectiveness",
    }
    if opera_apfd <= baseline_apfd:
        raise AssertionError(result)
    if opera[0].name != "conv-output-pad":
        raise AssertionError(f"unexpected first case: {opera[0].name}")
    Path("results").mkdir(exist_ok=True)
    Path("results/l2-mini.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

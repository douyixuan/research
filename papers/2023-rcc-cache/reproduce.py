#!/usr/bin/env python3
"""Deterministic mechanism-level reproduction for RCC.

This is deliberately a scoped model, not the Perses implementation.  It exercises the
paper's two RCC invariants on a reduction trace: canonical compact encoding of a
subsequence and safe removal of stale cache entries when the current minimum shrinks.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def is_subsequence(xs: tuple[str, ...], ys: tuple[str, ...]) -> bool:
    """Return whether xs is a subsequence of ys."""
    it = iter(ys)
    return all(any(y == x for y in it) for x in xs)


def encode_intervals(base: tuple[str, ...], variant: tuple[str, ...]) -> tuple[tuple[int, int], ...]:
    """Greedily produce a canonical list of slicing intervals in base."""
    positions: list[int] = []
    j = 0
    for i, tok in enumerate(base):
        if j < len(variant) and tok == variant[j]:
            positions.append(i)
            j += 1
    if j != len(variant):
        raise ValueError("variant is not a subsequence of base")

    intervals: list[list[int]] = []
    for pos in positions:
        if not intervals or pos != intervals[-1][1] + 1:
            intervals.append([pos, pos])
        else:
            intervals[-1][1] = pos
    return tuple((a, b) for a, b in intervals)


def decode_intervals(base: tuple[str, ...], key: tuple[tuple[int, int], ...]) -> tuple[str, ...]:
    out: list[str] = []
    for lo, hi in key:
        out.extend(base[lo : hi + 1])
    return tuple(out)


def property_oracle(program: tuple[str, ...]) -> bool:
    # Synthetic failure-preserving property: all twelve X fragments plus B are required.
    return program.count("X") == 12 and program[-1:] == ("B",)


def run_trace(use_cache: bool) -> dict:
    current = ("A",) + ("X",) * 12 + ("B",)
    oracle_calls = 0
    cache: set[tuple[tuple[int, int], ...]] = set()
    refresh_removed = 0
    hits = 0

    def query(candidate: tuple[str, ...]) -> bool:
        nonlocal oracle_calls, hits
        if not use_cache:
            oracle_calls += 1
            return property_oracle(candidate)
        key = encode_intervals(current, candidate)
        if key in cache:
            hits += 1
            return False
        cache.add(key)
        oracle_calls += 1
        return property_oracle(candidate)

    # Phase 1: deleting any one of twelve adjacent identical X fragments produces
    # the same textual/token variant.  All are rejected by the property oracle.
    for i in range(1, 13):
        candidate = current[:i] + current[i + 1 :]
        assert not query(candidate)

    # An unrelated deletion is accepted, becoming the new minimum.
    accepted = current[1:]
    assert query(accepted)

    if use_cache:
        old_current = current
        reconstructed = [decode_intervals(old_current, k) for k in cache]
        kept = [v for v in reconstructed if is_subsequence(v, accepted)]
        refresh_removed = len(reconstructed) - len(kept)
        current = accepted
        cache = {encode_intervals(current, v) for v in kept}
    else:
        current = accepted

    # Phase 2 repeats the duplicate-deletion pattern under the new minimum.
    for i in range(0, 12):
        candidate = current[:i] + current[i + 1 :]
        assert not query(candidate)

    return {
        "oracle_calls": oracle_calls,
        "cache_hits": hits,
        "refresh_removed_entries": refresh_removed,
        "final_min_tokens": len(current),
        "final_cache_entries": len(cache) if use_cache else None,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    no_cache = run_trace(False)
    rcc = run_trace(True)

    assert no_cache["oracle_calls"] == 25
    assert rcc["oracle_calls"] == 3
    assert rcc["cache_hits"] == 22
    assert rcc["refresh_removed_entries"] >= 1

    base = ("A",) + ("X",) * 12 + ("B",)
    duplicate_variant = base[:1] + base[2:]
    key = encode_intervals(base, duplicate_variant)
    assert decode_intervals(base, key) == duplicate_variant

    summary = {
        "level": "scoped L2 mechanism model (not Perses, not L1/L3)",
        "trace": "12 duplicate rejected deletions -> accepted minimum shrink -> 12 duplicate rejected deletions",
        "no_cache": no_cache,
        "rcc_model": rcc,
        "oracle_call_reduction_pct": round(
            100.0 * (no_cache["oracle_calls"] - rcc["oracle_calls"]) / no_cache["oracle_calls"], 2
        ),
        "compact_key_example": [list(x) for x in key],
        "invariants_checked": [
            "variant is represented losslessly as slicing intervals of current minimum",
            "identical variants map to one canonical cache key",
            "entries that are not subsequences of a new minimum are safely removed",
        ],
    }
    (RESULTS / "mechanism-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

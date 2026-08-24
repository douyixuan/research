#!/usr/bin/env python3
"""Fresh, minimal DDMT mechanism reproduction.

No ground-truth output is used by mrtest.  The target is intentionally buggy:
for inputs containing the trigger '@', adding a trailing comment leaks comment
text into the token analysis.  A correct tokenizer would be invariant to that
metamorphic transformation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"


def buggy_tokenizer(text: str) -> list[str]:
    # Normal behavior: comments are ignored.
    code, _, comment = text.partition("#")
    tokens = code.split()
    # Seeded silent bug: for source programs containing '@', comments leak into
    # the output.  There is no crash and no expected-output oracle in mrtest.
    if "@" in code and comment:
        tokens.extend(comment.split())
    return tokens


def follow_up(text: str) -> str:
    return text + " # harmless comment"


def mrtest(text: str, counter: list[int]) -> str:
    counter[0] += 1
    source = buggy_tokenizer(text)
    follow = buggy_tokenizer(follow_up(text))
    # MR: adding a comment must not change the token analysis.
    return FAIL if source != follow else PASS


def ddmin(items: list[str], test) -> list[str]:
    assert test(items) == FAIL
    n = 2
    current = items[:]
    while len(current) >= 2:
        subset_len = (len(current) + n - 1) // n
        some_reduction = False
        for start in range(0, len(current), subset_len):
            complement = current[:start] + current[start + subset_len :]
            if complement and test(complement) == FAIL:
                current = complement
                n = max(n - 1, 2)
                some_reduction = True
                break
        if some_reduction:
            continue
        if n >= len(current):
            break
        n = min(len(current), n * 2)
    return current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original_tokens = ["noise", "alpha", "@", "beta", "unused", "tail"]
    original = " ".join(original_tokens)
    calls = [0]

    def test(parts: list[str]) -> str:
        return mrtest(" ".join(parts), calls)

    assert test(original_tokens) == FAIL, "seed must violate the MR"
    reduced_tokens = ddmin(original_tokens, test)
    reduced = " ".join(reduced_tokens)
    assert test(reduced_tokens) == FAIL
    assert reduced_tokens == ["@"], f"expected 1-minimal trigger, got {reduced_tokens!r}"

    # Demonstrate the crucial oracle-less point: the source execution itself is
    # perfectly ordinary. The property comes only from the source/follow-up relation.
    source_output = buggy_tokenizer(reduced)
    follow_output = buggy_tokenizer(follow_up(reduced))
    assert source_output == ["@"]
    assert source_output != follow_output

    report = {
        "status": "pass",
        "level": "scoped L2 mechanism",
        "oracle_used_by_reducer": False,
        "metamorphic_relation": "adding a trailing comment preserves token analysis",
        "original": original,
        "original_elements": len(original_tokens),
        "reduced": reduced,
        "reduced_elements": len(reduced_tokens),
        "mrtest_calls": calls[0],
        "source_output": source_output,
        "follow_up_output": follow_output,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

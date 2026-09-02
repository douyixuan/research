#!/usr/bin/env python3
"""Independent scoped-L2 reproduction of PROJ's control architecture.

This is not the authors' PROJ implementation and it does not use an LLM.
A deterministic scripted proposer stands in for the reducer/reflector agents so
CI can exercise the full propose -> oracle -> feedback -> distill -> replay loop.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

TRAIN = r'''
#include <stdio.h>
int identity(int x) { return x; }
int twice(int x) { return x + x; }
int unused_helper(int x) { return x * 99; }
int main(void) {
    int noise = unused_helper(3);
    int value = identity(twice(21));
    if (value == 42) {
        printf("TRIGGER:%d\n", value);
    }
    return 0;
}
'''.strip() + "\n"

HELDOUT = r'''
#include <stdio.h>
int identity(int x) { return x; }
int dead_calc(int x) { return x - 777; }
int main(void) {
    int junk = dead_calc(1000);
    int answer = identity(42);
    if (answer == 42) {
        printf("TRIGGER:%d\n", answer);
    }
    return 0;
}
'''.strip() + "\n"

EXPECTED = "TRIGGER:42\n"

TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||\S")


def tokens(src: str) -> int:
    return len(TOKEN_RE.findall(src))


@dataclass
class Oracle:
    calls: int = 0

    def holds(self, src: str) -> bool:
        self.calls += 1
        with tempfile.TemporaryDirectory() as td_raw:
            td = Path(td_raw)
            c = td / "case.c"
            exe = td / "case"
            c.write_text(src)
            cp = subprocess.run(
                ["cc", "-std=c11", "-O2", str(c), "-o", str(exe)],
                capture_output=True,
                text=True,
            )
            if cp.returncode != 0:
                return False
            try:
                rp = subprocess.run(
                    [str(exe)], capture_output=True, text=True, timeout=5
                )
            except subprocess.TimeoutExpired:
                return False
            return rp.returncode == 0 and rp.stdout == EXPECTED


Transform = Callable[[str], str]


def remove_dead_helper(src: str) -> str:
    """Remove a one-use helper whose result is assigned to an unused local.

    This is deliberately small but name-agnostic, so the exact same learned
    strategy can replay on the differently named held-out fixture.
    """
    for dm in re.finditer(r"\nint ([A-Za-z_]\w*)\(int x\) \{ return [^;\n]+; \}\n", src):
        fn = dm.group(1)
        # Ignore semantic helpers that feed observable computation.
        am = re.search(rf"\s*int ([A-Za-z_]\w*) = {re.escape(fn)}\([^;\n]+\);\n", src)
        if not am:
            continue
        var = am.group(1)
        if len(re.findall(rf"\b{re.escape(var)}\b", src)) != 1:
            continue
        if len(re.findall(rf"\b{re.escape(fn)}\s*\(", src)) != 2:
            continue
        out = src[: am.start()] + "\n" + src[am.end() :]
        # Re-find the definition after removing the assignment.
        out = re.sub(
            rf"\nint {re.escape(fn)}\(int x\) \{{ return [^;\n]+; \}}\n",
            "\n",
            out,
            count=1,
        )
        return out
    return src


def inline_identity(src: str) -> str:
    out = re.sub(r"\nint identity\(int x\) \{ return x; \}\n", "\n", src)
    return re.sub(r"\bidentity\(([^()]+|\([^()]*\))\)", r"\1", out)


def explore_expand_twice(src: str) -> str:
    # Exploration mode may accept a temporary size increase. Keep twice() in
    # place for one step; later passes can fold the new expression and remove it.
    return src.replace("twice(21)", "(21 + 21)")


def fold_21_plus_21(src: str) -> str:
    return src.replace("(21 + 21)", "42")


def remove_twice(src: str) -> str:
    if "twice(" in src.replace("int twice(int x)", ""):
        return src
    return re.sub(r"\nint twice\(int x\) \{ return x \+ x; \}\n", "\n", src)


def break_property(src: str) -> str:
    return src.replace('printf("TRIGGER:%d\\n", value);', 'printf("NOPE:%d\\n", value);')


TRANSFORMS: dict[str, Transform] = {
    "remove_dead_helper": remove_dead_helper,
    "inline_identity": inline_identity,
    "explore_expand_twice": explore_expand_twice,
    "fold_21_plus_21": fold_21_plus_21,
    "remove_twice": remove_twice,
    "break_property": break_property,
}


@dataclass
class Proposal:
    name: str
    mode: str
    rationale: str


@dataclass
class Event:
    proposal: str
    mode: str
    before_tokens: int
    after_tokens: int
    accepted: bool
    reason: str


# Deterministic stand-in for the Reducer Agent. The ordering intentionally
# includes one invalid proposal and one temporary expansion.
AGENT_PLAN = [
    Proposal("remove_dead_helper", "default", "drop a dead helper and its unused result"),
    Proposal("break_property", "default", "probe whether the observable marker is essential"),
    Proposal("explore_expand_twice", "explore", "expose constant structure before simplifying"),
    Proposal("fold_21_plus_21", "default", "constant-fold the exposed expression"),
    Proposal("remove_twice", "default", "remove helper after its last call disappears"),
    Proposal("inline_identity", "default", "inline a semantic no-op wrapper"),
]


def run_agent(src: str, oracle: Oracle) -> tuple[str, list[Event], list[str]]:
    assert oracle.holds(src), "training fixture must initially satisfy the property"
    current = src
    events: list[Event] = []
    accepted_names: list[str] = []
    exploration_budget = 16  # maximum temporary token increase

    for p in AGENT_PLAN:
        candidate = TRANSFORMS[p.name](current)
        before, after = tokens(current), tokens(candidate)
        if candidate == current:
            events.append(Event(p.name, p.mode, before, after, False, "no-op"))
            continue

        if p.mode == "default" and after > before:
            events.append(Event(p.name, p.mode, before, after, False, "default mode cannot grow"))
            continue
        if p.mode == "explore" and after - before > exploration_budget:
            events.append(Event(p.name, p.mode, before, after, False, "exploration budget exceeded"))
            continue

        if oracle.holds(candidate):
            current = candidate
            accepted_names.append(p.name)
            events.append(Event(p.name, p.mode, before, after, True, p.rationale))
        else:
            events.append(Event(p.name, p.mode, before, after, False, "property checker rejected"))

    assert oracle.holds(current)
    return current, events, accepted_names


def reflect(accepted_names: list[str]) -> list[str]:
    """Distill reusable, deterministic strategies from successful history.

    The real PROJ uses an LLM reflector. Here we deliberately keep only passes
    whose match/rewrite is fixture-agnostic enough to replay on held-out input.
    """
    reusable = []
    for name in accepted_names:
        if name in {"inline_identity", "remove_dead_helper"} and name not in reusable:
            reusable.append(name)
    return reusable


def replay_learned(src: str, strategy_names: list[str], oracle: Oracle) -> tuple[str, list[Event]]:
    assert oracle.holds(src), "held-out fixture must initially satisfy the property"
    current = src
    events: list[Event] = []
    while True:
        changed = False
        for name in strategy_names:
            candidate = TRANSFORMS[name](current)
            before, after = tokens(current), tokens(candidate)
            if candidate == current:
                continue
            if after <= before and oracle.holds(candidate):
                current = candidate
                changed = True
                events.append(Event(name, "learned", before, after, True, "property-guarded replay"))
            else:
                events.append(Event(name, "learned", before, after, False, "replay rejected"))
        if not changed:
            break
    assert oracle.holds(current)
    return current, events


def main() -> None:
    train_oracle = Oracle()
    train_final, train_events, accepted = run_agent(TRAIN, train_oracle)
    learned = reflect(accepted)

    held_oracle = Oracle()
    held_final, held_events = replay_learned(HELDOUT, learned, held_oracle)

    train_before, train_after = tokens(TRAIN), tokens(train_final)
    held_before, held_after = tokens(HELDOUT), tokens(held_final)

    # Assertions make the CI lane meaningful rather than descriptive only.
    assert train_after < train_before
    assert any(not e.accepted and e.proposal == "break_property" for e in train_events)
    assert any(e.accepted and e.mode == "explore" for e in train_events)
    assert set(learned) == {"remove_dead_helper", "inline_identity"}
    assert held_after < held_before
    assert held_oracle.holds(held_final)

    report = {
        "scope": "independent scoped L2 mechanism; scripted proposer replaces LLM",
        "train": {
            "before_tokens": train_before,
            "after_tokens": train_after,
            "reduction_pct": round(100.0 * (train_before - train_after) / train_before, 2),
            "oracle_calls": train_oracle.calls,
            "events": [asdict(e) for e in train_events],
        },
        "reflector": {"learned_strategies": learned},
        "heldout": {
            "before_tokens": held_before,
            "after_tokens": held_after,
            "reduction_pct": round(100.0 * (held_before - held_after) / held_before, 2),
            "oracle_calls": held_oracle.calls,
            "events": [asdict(e) for e in held_events],
        },
        "limitations": [
            "No authors' PROJ artifact is public as of 2026-09-02.",
            "The reducer and reflector agents are deterministic scripted stand-ins, not LLMs.",
            "Fixtures are fresh controlled C programs, not the paper's 90 benchmark bugs.",
        ],
    }
    out = RESULTS / "pipeline_l2.json"
    out.write_text(json.dumps(report, indent=2) + "\n")

    print(f"train_tokens={train_before}->{train_after}")
    print(f"train_oracle_calls={train_oracle.calls}")
    print("train_accepted=" + ",".join(e.proposal for e in train_events if e.accepted))
    print("train_rejected=" + ",".join(e.proposal for e in train_events if not e.accepted))
    print("learned_strategies=" + ",".join(learned))
    print(f"heldout_tokens={held_before}->{held_after}")
    print(f"heldout_oracle_calls={held_oracle.calls}")
    print("PASS: propose/check/explore/distill/property-guarded-replay completed end-to-end.")


if __name__ == "__main__":
    main()

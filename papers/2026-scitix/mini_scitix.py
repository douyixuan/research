#!/usr/bin/env python3
"""Mechanism-level reproduction of Scitix's motivating example.

This is intentionally NOT the authors' implementation. It isolates the paper's two
main ideas on a small synthetic knowledge base:
  1) map directly-identifiable missing types to Any;
  2) start without supertype constraints and add them back only when satisfiable.

The competing Intent entries mirror the ambiguity discussed in the Scitix thesis,
but signatures other than the Android/Class relationship are synthetic so that this
file stays self-contained and deterministic.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Constructor:
    owner: str
    arg0: str
    arg1: str


ANDROID_INTENT = Constructor(
    owner="android.content.Intent",
    arg0="android.content.Context",
    arg1="java.lang.Class",
)

# A synthetic competing candidate with the same simple name but an incompatible
# second constructor parameter. The paper only requires that the competing Redis
# Intent does not satisfy the java.lang.Class constraint; no exact Redis signature
# is claimed here.
REDIS_INTENT = Constructor(
    owner="com.lambdaworks.redis.synthetic.Intent",
    arg0="redis.synthetic.Context",
    arg1="redis.synthetic.Target",
)


def make_kb(noise: int) -> list[Constructor]:
    kb = [ANDROID_INTENT, REDIS_INTENT]
    for i in range(noise):
        kb.append(
            Constructor(
                owner=f"noise.pkg{i}.Intent",
                arg0=f"noise.pkg{i}.Context",
                arg1=f"noise.pkg{i}.Target",
            )
        )
    return kb


def strict_snr_like(kb: list[Constructor]) -> list[str]:
    """Require every extracted type relationship to be concretely satisfiable.

    The motivating snippet contains a user-defined Main type absent from the KB.
    Therefore the full constraint set is unsatisfiable even if the correct Intent
    candidate is present.
    """
    main_type_exists = False
    if not main_type_exists:
        return []
    return [c.owner for c in kb if c.arg1 == "java.lang.Class"]


def base_scitix_candidates(kb: list[Constructor]) -> list[Constructor]:
    """Solve class/method/method_param constraints after Main -> Any.

    Supertype constraints are withheld initially, so all same-name constructor
    candidates remain possible.
    """
    return list(kb)


def add_supertype_if_satisfiable(
    candidates: list[Constructor], constraint: str
) -> tuple[list[Constructor], bool]:
    if constraint == "arg0_supertype_of_Main":
        # Main is unknown. Requiring a concrete subtype/supertype witness makes
        # the current set unsatisfiable, so Scitix should reject this constraint.
        filtered: list[Constructor] = []
    elif constraint == "arg1_supertype_of_java.lang.Class":
        filtered = [c for c in candidates if c.arg1 == "java.lang.Class"]
    else:
        raise ValueError(constraint)

    if filtered:
        return filtered, True
    return candidates, False


def scitix_like(kb: list[Constructor]) -> dict:
    candidates = base_scitix_candidates(kb)
    accepted: list[str] = []
    rejected: list[str] = []

    # Deliberately try the unknown-dependent constraint first. A correct
    # satisfiability-preserving loop must reject it without poisoning later work.
    for constraint in [
        "arg0_supertype_of_Main",
        "arg1_supertype_of_java.lang.Class",
    ]:
        candidates, keep = add_supertype_if_satisfiable(candidates, constraint)
        (accepted if keep else rejected).append(constraint)

    return {
        "initial_candidates": [c.owner for c in kb],
        "accepted_supertype_constraints": accepted,
        "rejected_supertype_constraints": rejected,
        "final_candidates": [c.owner for c in candidates],
    }


def run(noise_sizes: list[int]) -> dict:
    rows = []
    for noise in noise_sizes:
        kb = make_kb(noise)

        t0 = time.perf_counter_ns()
        strict = strict_snr_like(kb)
        t1 = time.perf_counter_ns()
        scitix = scitix_like(kb)
        t2 = time.perf_counter_ns()

        assert strict == [], "strict full-constraint model should be unsatisfiable"
        assert scitix["final_candidates"] == ["android.content.Intent"]
        assert scitix["accepted_supertype_constraints"] == [
            "arg1_supertype_of_java.lang.Class"
        ]
        assert scitix["rejected_supertype_constraints"] == [
            "arg0_supertype_of_Main"
        ]

        rows.append(
            {
                "noise_candidates": noise,
                "kb_candidates_with_simple_name_Intent": len(kb),
                "strict_full_constraint_candidates": strict,
                "scitix_final_candidates": scitix["final_candidates"],
                "strict_runtime_ns": t1 - t0,
                "scitix_runtime_ns": t2 - t1,
            }
        )

    detailed = scitix_like(make_kb(8))
    return {
        "reproduction_level": "scoped-L2-mechanism-model",
        "claim_boundary": (
            "This reruns a fresh self-contained model of the two Scitix mechanisms; "
            "it does not execute the authors' Java/MariaDB artifact or reproduce paper F1/runtime."
        ),
        "motivating_property": {
            "strict_full_constraint_result": [],
            "scitix_like_result": detailed,
        },
        "scale_smoke": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/mechanism.json")
    parser.add_argument(
        "--noise-sizes", default="0,10,100,1000,10000", help="comma-separated"
    )
    args = parser.parse_args()

    noise_sizes = [int(x) for x in args.noise_sizes.split(",") if x]
    report = run(noise_sizes)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")

    final = report["motivating_property"]["scitix_like_result"]["final_candidates"]
    print(f"strict full constraints -> UNSAT")
    print(f"Scitix-like Any + iterative constraints -> {final}")
    print(f"scale smoke sizes -> {noise_sizes}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

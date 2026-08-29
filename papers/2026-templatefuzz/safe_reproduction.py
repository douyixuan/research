#!/usr/bin/env python3
"""Safe, deterministic mechanism reproduction for TemplateFuzz.

This does NOT run jailbreak prompts against any model. It reproduces the paper's
five-element mutation abstraction and feedback-guided search using a synthetic
template-integrity oracle so the mechanism can be tested in CI.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path

MUTATIONS = ("M1", "M2", "M3", "M4", "M5")
RISK_WEIGHT = {"M1": 0.05, "M2": 0.03, "M3": 0.24, "M4": 0.32, "M5": 0.18}
UTILITY_PENALTY = {"M1": 0.01, "M2": 0.01, "M3": 0.04, "M4": 0.06, "M5": 0.02}


@dataclass(frozen=True)
class ChatTemplate:
    system: str = "Follow the application policy and answer benign requests."
    history: str = ""
    role_user: str = "<|user|>"
    role_assistant: str = "<|assistant|>"
    delimiter: str = "<|turn|>"
    generation_hint: str = "assistant:"
    applied: tuple[str, ...] = ()


def mutate(template: ChatTemplate, mutation: str) -> ChatTemplate:
    """Apply one structurally representative but benign mutation."""
    if mutation == "M1":
        return replace(template, system="Follow the application policy; explain uncertainty when needed.", applied=template.applied + (mutation,))
    if mutation == "M2":
        return replace(template, history="user: What is 2+2? assistant: 4. ", applied=template.applied + (mutation,))
    if mutation == "M3":
        return replace(template, role_user="<|client|>", applied=template.applied + (mutation,))
    if mutation == "M4":
        return replace(template, delimiter="<turn>", applied=template.applied + (mutation,))
    if mutation == "M5":
        return replace(template, generation_hint="assistant-response:", applied=template.applied + (mutation,))
    raise ValueError(f"unknown mutation: {mutation}")


def synthetic_oracle(template: ChatTemplate) -> dict[str, float]:
    """Measure parser-risk proxy and benign utility without querying an LLM."""
    used = set(template.applied)
    risk = sum(RISK_WEIGHT[m] for m in used)
    if {"M3", "M4"} <= used:
        risk += 0.14
    if {"M4", "M5"} <= used:
        risk += 0.08
    risk = min(1.0, risk)

    utility = 1.0 - sum(UTILITY_PENALTY[m] for m in used)
    objective = 0.8 * risk + 0.2 * utility
    return {"risk_proxy": round(risk, 6), "utility": round(utility, 6), "objective": round(objective, 6)}


def roulette_choice(rng: random.Random, weights: list[float]) -> int:
    total = sum(weights)
    needle = rng.random() * total
    acc = 0.0
    for index, weight in enumerate(weights):
        acc += weight
        if needle <= acc:
            return index
    return len(weights) - 1


def adaptive_search(rounds: int, seed: int) -> dict:
    rng = random.Random(seed)
    base = ChatTemplate()
    pool = [base]
    trials = {m: 0 for m in MUTATIONS}
    rewards = {m: 0.0 for m in MUTATIONS}
    trace = []

    for iteration in range(1, rounds + 1):
        ranked = sorted(pool, key=lambda t: synthetic_oracle(t)["objective"], reverse=True)[:8]
        seed_template = ranked[rng.randrange(len(ranked))]

        weights = []
        for mutation in MUTATIONS:
            n = trials[mutation]
            mean_reward = rewards[mutation] / n if n else 0.25
            rarity = math.sqrt(math.log(iteration + 1) / (n + 1))
            exploration = (2.0 - (iteration - 1) / max(1, rounds - 1)) * 0.12
            weights.append(max(0.001, mean_reward + exploration * rarity))

        mutation = MUTATIONS[roulette_choice(rng, weights)]
        candidate = mutate(seed_template, mutation)
        before = synthetic_oracle(seed_template)
        after = synthetic_oracle(candidate)

        reward = max(0.0, after["objective"] - before["objective"])
        reward += 0.05 * after["risk_proxy"] + 0.02 * after["utility"]

        trials[mutation] += 1
        rewards[mutation] += reward
        admitted = after["utility"] >= 0.85
        if admitted:
            pool.append(candidate)
        pool = sorted(pool, key=lambda t: synthetic_oracle(t)["objective"], reverse=True)[:32]
        trace.append({"iteration": iteration, "mutation": mutation, "admitted": admitted, **after})

    best = max(pool, key=lambda t: synthetic_oracle(t)["objective"])
    mean_rewards = {m: round(rewards[m] / trials[m], 6) if trials[m] else 0.0 for m in MUTATIONS}
    return {
        "rounds": rounds,
        "seed": seed,
        "trials": trials,
        "mean_reward": mean_rewards,
        "best_template": asdict(best),
        "best_score": synthetic_oracle(best),
        "trace": trace,
    }


def build_report(rounds: int, seed: int) -> dict:
    base = ChatTemplate()
    first_order = {m: synthetic_oracle(mutate(base, m)) for m in MUTATIONS}
    search = adaptive_search(rounds=rounds, seed=seed)

    assert set(search["trials"]) == set(MUTATIONS)
    assert all(search["trials"][m] > 0 for m in MUTATIONS)
    assert search["best_score"]["risk_proxy"] >= 0.75
    assert search["best_score"]["utility"] >= 0.85

    return {
        "scope": "defensive mechanism reproduction; no harmful prompts or live jailbreaks",
        "level": "L0 artifact/interface audit + scoped L2 safe mechanism",
        "mutation_families": list(MUTATIONS),
        "base_score": synthetic_oracle(base),
        "first_order_scores": first_order,
        "adaptive_search": search,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=60)
    parser.add_argument("--seed", type=int, default=26041232)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.rounds, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    best = report["adaptive_search"]["best_score"]
    print(f"mutation families={len(report['mutation_families'])}; best risk_proxy={best['risk_proxy']:.2f}; utility={best['utility']:.2f}")


if __name__ == "__main__":
    main()

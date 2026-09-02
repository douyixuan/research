#!/usr/bin/env python3
"""Manual live-LLM scaffold for the next PROJ reproduction step.

Requires an OpenAI-compatible chat-completions endpoint. It is intentionally
not part of the default CI lane because model/API drift makes it nondeterministic.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import asdict
from pathlib import Path

from pipeline_l2 import HELDOUT, TRAIN, Event, Oracle, tokens

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

ENDPOINT = os.environ.get("PROJ_LLM_ENDPOINT", "")
API_KEY = os.environ.get("PROJ_LLM_API_KEY", "")
MODEL = os.environ.get("PROJ_LLM_MODEL", "")


def require_config() -> None:
    missing = [
        name
        for name, value in {
            "PROJ_LLM_ENDPOINT": ENDPOINT,
            "PROJ_LLM_API_KEY": API_KEY,
            "PROJ_LLM_MODEL": MODEL,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit("missing required configuration: " + ", ".join(missing))


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def chat(system: str, user: str) -> dict:
    payload = json.dumps(
        {
            "model": MODEL,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    text = data["choices"][0]["message"]["content"]
    return extract_json(text)


def reducer_agent(src: str, oracle: Oracle, attempts: int = 6) -> tuple[str, list[dict]]:
    current = src
    trace: list[dict] = []
    assert oracle.holds(current)
    feedback = "No previous attempt."
    exploration_used = False

    for _ in range(attempts):
        proposal = chat(
            "You are a C program-reduction agent. Return ONLY JSON with keys candidate, rationale, mode. "
            "mode must be default or explore. Preserve the exact observable stdout TRIGGER:42\\n. "
            "Default proposals must not increase lexical token count. Explore may temporarily grow once.",
            f"Current program:\n```c\n{current}\n```\nPrevious harness feedback: {feedback}",
        )
        prev = current
        candidate = str(proposal.get("candidate", ""))
        mode = str(proposal.get("mode", "default"))
        rationale = str(proposal.get("rationale", ""))
        before, after = tokens(prev), tokens(candidate)

        accepted = False
        reason = ""
        if not candidate:
            reason = "empty candidate"
        elif mode not in {"default", "explore"}:
            reason = "invalid mode"
        elif mode == "default" and after > before:
            reason = "default mode grew"
        elif mode == "explore" and exploration_used:
            reason = "exploration budget already used"
        elif mode == "explore" and after - before > 32:
            reason = "exploration growth >32 tokens"
        elif oracle.holds(candidate):
            current = candidate
            accepted = True
            exploration_used |= mode == "explore"
            reason = "property checker accepted"
        else:
            reason = "property checker rejected"

        trace.append(
            {
                "mode": mode,
                "rationale": rationale,
                "before_tokens": before,
                "after_tokens": after,
                "accepted": accepted,
                "reason": reason,
                "before": prev,
                "candidate": candidate,
                "accepted_source": current,
            }
        )
        feedback = f"{reason}; token_count={tokens(current)}"

    assert oracle.holds(current)
    return current, trace


def reflector(trace: list[dict]) -> dict:
    accepted = [t for t in trace if t["accepted"]]
    if not accepted:
        raise SystemExit("no accepted transitions; cannot reflect")
    compact = [
        {
            "before": t["before"],
            "after": t["candidate"],
            "rationale": t["rationale"],
        }
        for t in accepted[-3:]
    ]
    return chat(
        "You are a reducer-strategy reflector. Infer ONE conservative reusable text rewrite from successful C reductions. "
        "Return ONLY JSON with keys pattern, replacement, description. pattern is a Python regular expression. "
        "Do not use lookbehind, backreferences in pattern, or patterns longer than 300 characters.",
        json.dumps(compact),
    )


def validate_strategy(strategy: dict, src: str, oracle: Oracle) -> tuple[str, Event]:
    pattern = str(strategy.get("pattern", ""))
    replacement = str(strategy.get("replacement", ""))
    if not pattern or len(pattern) > 300 or "(?<=" in pattern or "(?<!" in pattern:
        raise SystemExit("reflector emitted disallowed regex")
    regex = re.compile(pattern, re.M | re.S)
    candidate = regex.sub(replacement, src, count=1)
    before, after = tokens(src), tokens(candidate)
    accepted = candidate != src and after <= before and oracle.holds(candidate)
    event = Event(
        "llm_reflected_regex",
        "learned",
        before,
        after,
        accepted,
        "property-guarded held-out replay" if accepted else "held-out replay rejected",
    )
    return (candidate if accepted else src), event


def main() -> None:
    require_config()
    train_oracle = Oracle()
    reduced, trace = reducer_agent(TRAIN, train_oracle)
    strategy = reflector(trace)
    held_oracle = Oracle()
    assert held_oracle.holds(HELDOUT)
    held_final, event = validate_strategy(strategy, HELDOUT, held_oracle)

    result = {
        "model": MODEL,
        "endpoint": ENDPOINT,
        "train_tokens": [tokens(TRAIN), tokens(reduced)],
        "train_oracle_calls": train_oracle.calls,
        "trace": trace,
        "strategy": strategy,
        "heldout_tokens": [tokens(HELDOUT), tokens(held_final)],
        "heldout_event": asdict(event),
        "heldout_oracle_calls": held_oracle.calls,
    }
    (RESULTS / "live_l2.json").write_text(json.dumps(result, indent=2) + "\n")
    if tokens(reduced) >= tokens(TRAIN):
        raise SystemExit("live reducer did not shrink training fixture")
    if not event.accepted:
        raise SystemExit("reflected strategy did not generalize to held-out fixture")
    print(f"train_tokens={tokens(TRAIN)}->{tokens(reduced)}")
    print(f"heldout_tokens={tokens(HELDOUT)}->{tokens(held_final)}")
    print("PASS: live LLM reducer + reflector + held-out property-guarded replay")


if __name__ == "__main__":
    main()

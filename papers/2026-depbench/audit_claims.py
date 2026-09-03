#!/usr/bin/env python3
import json
from pathlib import Path

TOTAL = 203
ECOSYSTEMS = {"npm/yarn": 68, "Maven/Java": 65, "Go": 40, "Cargo/Rust": 20, "Python": 10}
PASS_COUNTS = {
    "Claude Code + GPT-5.5": 71,
    "Codex + GPT-5.5": 104,
    "Copilot CLI + GPT-5.5": 99,
    "OpenCode + GPT-5.5": 80,
    "Claude Code + Claude Opus 4.8": 79,
    "Copilot CLI + Claude Opus 4.8": 83,
    "OpenCode + Claude Opus 4.8": 80,
    "Claude Code + Gemini 3.5 Flash": 53,
    "Copilot CLI + Gemini 3.5 Flash": 52,
    "OpenCode + Gemini 3.5 Flash": 51,
}
CODEX_ECOSYSTEM = {"npm/yarn": 27, "Maven/Java": 46, "Go": 20, "Cargo/Rust": 6, "Python": 5}

def pct(n, d):
    return round(100.0 * n / d, 1)

assert sum(ECOSYSTEMS.values()) == TOTAL
assert sum(CODEX_ECOSYSTEM.values()) == PASS_COUNTS["Codex + GPT-5.5"] == 104
assert pct(104, TOTAL) == 51.2
assert 104 - 71 == 33
assert pct(33, TOTAL) == 16.3
assert pct(322, 521) == 61.8
assert pct(156, TOTAL) == 76.8

summary = {
    "reproduction_level": "L0 claim arithmetic audit (paper-transcribed values; not L1)",
    "total_tasks": TOTAL,
    "ecosystem_sum": sum(ECOSYSTEMS.values()),
    "best_configuration": "Codex + GPT-5.5",
    "best_passes": 104,
    "best_pass_rate_percent": pct(104, TOTAL),
    "gpt55_codex_vs_claude_code_spread_tasks": 33,
    "gpt55_codex_vs_claude_code_spread_percentage_points": pct(33, TOTAL),
    "visible_test_pass_before_hidden_failure": {"count": 322, "analyzed_nonpasses": 521, "percent": pct(322, 521)},
    "primary_direct_behavior_tasks": {"count": 156, "total": TOTAL, "percent": pct(156, TOTAL)},
    "codex_gpt55_ecosystem_passes": CODEX_ECOSYSTEM,
}

out = Path(__file__).resolve().parent / "results" / "claim-audit.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))

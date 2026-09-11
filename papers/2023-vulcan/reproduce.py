#!/usr/bin/env python3
"""Scoped L2 mechanism reproduction for Vulcan's non-deletion transformation idea.

This is intentionally not the paper implementation. It demonstrates the core
mechanism on a fresh C case: deletion reaches a 1-minimal program, an identifier
replacement preserves the property without shrinking immediately, and a second
deletion pass can then remove a formerly necessary declaration.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
INPUT = HERE / "case" / "small.c"

HEADER = "#include <stdio.h>\n\nint main(void) {\n"
FOOTER = "}\n"
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||[-+*/%=;(),{}]")
DECL_RE = re.compile(r"^\s*int\s+([A-Za-z_]\w*)\s*=.*;\s*$")


class Oracle:
    def __init__(self, cc: str):
        self.cc = cc
        self.calls = 0

    def test(self, lines: list[str]) -> bool:
        self.calls += 1
        src = render(lines)
        with tempfile.TemporaryDirectory(prefix="vulcan-") as td:
            td = Path(td)
            cfile = td / "small.c"
            exe = td / "small.out"
            cfile.write_text(src)
            cp = subprocess.run(
                [self.cc, "-O0", "-Wall", "-Werror", str(cfile), "-o", str(exe)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if cp.returncode != 0:
                return False
            rp = subprocess.run([str(exe)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return rp.returncode == 0 and rp.stdout == "42\n"


def render(lines: list[str]) -> str:
    return HEADER + "".join(f"  {line.strip()}\n" for line in lines) + FOOTER


def parse_fixture() -> list[str]:
    text = INPUT.read_text()
    body = text.split("int main(void) {", 1)[1].rsplit("}", 1)[0]
    return [line.strip() for line in body.splitlines() if line.strip()]


def deletion_fixpoint(lines: list[str], oracle: Oracle) -> list[str]:
    out = list(lines)
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            candidate = out[:i] + out[i + 1 :]
            if oracle.test(candidate):
                out = candidate
                changed = True
                break
    return out


def is_one_minimal(lines: list[str], oracle: Oracle) -> bool:
    return all(not oracle.test(lines[:i] + lines[i + 1 :]) for i in range(len(lines)))


def identifier_replacement_once(lines: list[str], oracle: Oracle) -> tuple[list[str], dict | None]:
    names = [m.group(1) for line in lines if (m := DECL_RE.match(line))]
    # Try replacing identifier uses with another already-declared identifier.
    for i, line in enumerate(lines):
        declared_here = DECL_RE.match(line)
        for old in names:
            if declared_here and declared_here.group(1) == old:
                # Keep the definition token itself unchanged, but initializer uses remain eligible.
                prefix = line[: declared_here.start(1) + len(old)]
                suffix = line[declared_here.start(1) + len(old) :]
                target_text = suffix
                base_prefix = prefix
            else:
                target_text = line
                base_prefix = ""
            if not re.search(rf"\b{re.escape(old)}\b", target_text):
                continue
            for new in names:
                if new == old:
                    continue
                replaced = re.sub(rf"\b{re.escape(old)}\b", new, target_text)
                new_line = base_prefix + replaced
                candidate = list(lines)
                candidate[i] = new_line
                if candidate != lines and oracle.test(candidate):
                    return candidate, {"line": i, "old": old, "new": new, "before": line, "after": new_line}
    return lines, None


def tokens(lines: list[str]) -> int:
    return len(TOKEN_RE.findall(render(lines)))


def main() -> int:
    cc = shutil.which("gcc") or shutil.which("clang")
    if not cc:
        raise SystemExit("gcc or clang is required")
    RESULTS.mkdir(exist_ok=True)

    original = parse_fixture()
    baseline_oracle = Oracle(cc)
    assert baseline_oracle.test(original), "fixture must satisfy the property"
    baseline = deletion_fixpoint(original, baseline_oracle)
    baseline_one_minimal = is_one_minimal(baseline, baseline_oracle)

    vulcan_oracle = Oracle(cc)
    assert vulcan_oracle.test(original)
    stage1 = deletion_fixpoint(original, vulcan_oracle)
    stage2, edit = identifier_replacement_once(stage1, vulcan_oracle)
    stage3 = deletion_fixpoint(stage2, vulcan_oracle)
    vulcan_one_minimal = is_one_minimal(stage3, vulcan_oracle)

    assert baseline_one_minimal, "deletion baseline should be 1-minimal at statement granularity"
    assert edit is not None, "expected a property-preserving identifier replacement"
    assert vulcan_oracle.test(stage3), "final transformed program must preserve property"
    assert len(stage3) < len(baseline), "non-deletion edit should unlock an additional deletion"

    baseline_text = render(baseline)
    vulcan_text = render(stage3)
    (RESULTS / "baseline.c").write_text(baseline_text)
    (RESULTS / "vulcan_like.c").write_text(vulcan_text)

    summary = {
        "level": "scoped L2 mechanism reproduction",
        "scope": "fresh synthetic C case; statement-level deletion + Vulcan-style identifier replacement; not paper implementation and not L1/L3",
        "compiler": subprocess.check_output([cc, "--version"], text=True).splitlines()[0],
        "property": "compile with -O0 -Wall -Werror, exit 0, stdout exactly 42\\n",
        "baseline": {
            "statements": len(baseline),
            "tokens": tokens(baseline),
            "bytes": len(baseline_text.encode()),
            "oracle_calls": baseline_oracle.calls,
            "one_minimal_at_statement_granularity": baseline_one_minimal,
        },
        "vulcan_like": {
            "statements": len(stage3),
            "tokens": tokens(stage3),
            "bytes": len(vulcan_text.encode()),
            "oracle_calls": vulcan_oracle.calls,
            "one_minimal_at_statement_granularity": vulcan_one_minimal,
            "accepted_non_deletion_edit": edit,
        },
        "delta": {
            "statements_removed_after_non_deletion_edit": len(baseline) - len(stage3),
            "token_reduction_pct_vs_deletion_baseline": round((tokens(baseline) - tokens(stage3)) * 100.0 / tokens(baseline), 4),
            "byte_reduction_pct_vs_deletion_baseline": round((len(baseline_text) - len(vulcan_text)) * 100.0 / len(baseline_text), 4),
        },
    }
    (RESULTS / "mechanism-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

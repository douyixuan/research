#!/usr/bin/env python3
"""Scoped L2 mechanism reproduction for DRReduce.

This is intentionally not the authors' implementation. It exercises the paper's
core mechanism with a real C compiler and property checker:

  delete provider alone -> invalid intermediate
  delete provider + reconstruct surviving use -> valid, property preserved

The experiment demonstrates why dependency reconstruction can unlock reductions
that a syntax-only deletion would reject.
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

ORIGINAL = r'''#include <stdio.h>

static int noise_value(void) {
  return 7;
}

static int trigger(int x) {
  return x == 42;
}

int main(void) {
  int irrelevant = noise_value();
  if (trigger(42)) {
    puts("BUG");
  }
  return irrelevant == 12345;
}
'''

# A syntax-only reducer that removes a declaration/provider without repairing
# users leaves an unresolved reference and is rejected by the compiler.
NAIVE_DELETE = ORIGINAL.replace(
    '''static int noise_value(void) {\n  return 7;\n}\n\n''', ""
)

# DRReduce-style dependency reconstruction: after deleting the provider, rewire
# its surviving use to a typed/default placeholder. For int, 0 is sufficient for
# this property checker because the bug-triggering behavior does not depend on
# the noise value.
RECONSTRUCTED = NAIVE_DELETE.replace("noise_value()", "0")

TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||[-+*/%<>{}();,=]")


def tokens(source: str) -> int:
    return len(TOKEN_RE.findall(source))


def compile_and_run(source: str, work: Path, name: str):
    src = work / f"{name}.c"
    exe = work / name
    src.write_text(source)
    cc = subprocess.run(
        ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)],
        text=True,
        capture_output=True,
    )
    if cc.returncode != 0:
        return {
            "compile_ok": False,
            "property_ok": False,
            "stderr": cc.stderr.strip(),
            "tokens": tokens(source),
        }
    run = subprocess.run([str(exe)], text=True, capture_output=True)
    return {
        "compile_ok": True,
        "property_ok": "BUG" in run.stdout,
        "stdout": run.stdout.strip(),
        "exit_code": run.returncode,
        "tokens": tokens(source),
    }


def main():
    with tempfile.TemporaryDirectory(prefix="mini-drreduce-") as td:
        work = Path(td)
        original = compile_and_run(ORIGINAL, work, "original")
        naive = compile_and_run(NAIVE_DELETE, work, "naive")
        reconstructed = compile_and_run(RECONSTRUCTED, work, "reconstructed")

    if not (original["compile_ok"] and original["property_ok"]):
        raise SystemExit("original program does not satisfy the property checker")
    if naive["compile_ok"]:
        raise SystemExit("naive provider deletion unexpectedly compiled")
    if not (reconstructed["compile_ok"] and reconstructed["property_ok"]):
        raise SystemExit("dependency-reconstructed candidate failed")
    if reconstructed["tokens"] >= original["tokens"]:
        raise SystemExit("reconstructed candidate did not reduce token count")

    summary = {
        "level": "scoped L2 mechanism reproduction",
        "not_authors_implementation": True,
        "property": "compiled executable prints BUG",
        "original": original,
        "syntax_only_provider_deletion": naive,
        "dependency_reconstructed_deletion": reconstructed,
        "observation": (
            "Deleting the provider alone is rejected because the intermediate program is invalid; "
            "rewiring the surviving use to a default value restores compilability while preserving the property."
        ),
    }
    out = Path(__file__).resolve().parent / "results" / "mechanism.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

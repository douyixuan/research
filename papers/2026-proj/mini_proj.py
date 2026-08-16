#!/usr/bin/env python3
'''Independent architecture smoke test inspired by PROJ.

This is NOT the PROJ implementation. It validates the paper's core harness
invariant: candidate rewrites only become durable after an executable property
checker accepts them, and learned strategies can be replayed to a fixpoint.
'''
from __future__ import annotations
import re
import subprocess
import tempfile
from pathlib import Path

SOURCE = r'''
#include <stdio.h>
int passthrough(int x) { return x; }
int unused(int z) { return z * 99; }
int main(void) {
  int noise = 123;
  int value = passthrough(7);
  printf("%d\n", value);
  return 0;
}
'''.strip() + "\n"

EXPECTED = "7\n"


def tokens(s: str) -> int:
    return len(re.findall(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||\S", s))


def property_holds(src: str) -> bool:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        c = td / "case.c"
        exe = td / "case"
        c.write_text(src)
        cp = subprocess.run(["cc", "-O2", str(c), "-o", str(exe)], capture_output=True, text=True)
        if cp.returncode != 0:
            return False
        rp = subprocess.run([str(exe)], capture_output=True, text=True, timeout=5)
        return rp.returncode == 0 and rp.stdout == EXPECTED


def remove_unused_function(src: str) -> str:
    return re.sub(r"\nint unused\(int z\) \{ return z \* 99; \}\n", "\n", src)


def inline_forwarder(src: str) -> str:
    out = re.sub(r"\nint passthrough\(int x\) \{ return x; \}\n", "\n", src)
    return re.sub(r"\bpassthrough\(([^()]+)\)", r"\1", out)


def remove_unused_local(src: str) -> str:
    return re.sub(r"\s*int noise = 123;\n", "\n", src)


STRATEGIES = [
    ("remove_unused_function", remove_unused_function),
    ("inline_forwarder", inline_forwarder),
    ("remove_unused_local", remove_unused_local),
]


def learned_reduce(src: str) -> tuple[str, list[str]]:
    assert property_holds(src)
    accepted = []
    current = src
    while True:
        changed = False
        for name, strategy in STRATEGIES:
            candidate = strategy(current)
            if candidate != current and property_holds(candidate) and tokens(candidate) <= tokens(current):
                current = candidate
                accepted.append(name)
                changed = True
        if not changed:
            break
    return current, accepted


if __name__ == "__main__":
    reduced, accepted = learned_reduce(SOURCE)
    assert property_holds(reduced)
    assert tokens(reduced) < tokens(SOURCE)
    print(f"before_tokens={tokens(SOURCE)}")
    print(f"after_tokens={tokens(reduced)}")
    print("accepted=" + ",".join(accepted))
    print("PASS: all durable rewrites were property-checked and replayed to a fixpoint.")

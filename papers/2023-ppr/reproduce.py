#!/usr/bin/env python3
import difflib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = (ROOT / "case/seed.c").read_text().splitlines()
VARIANT = (ROOT / "case/variant.c").read_text().splitlines()
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|\+\+|--|&&|\|\||[-+*/%<>=!&|^~?:;,.(){}\[\]]")


def token_count(lines):
    return len(TOKEN_RE.findall("\n".join(lines)))


def statement_candidates(lines):
    return [i for i, line in enumerate(lines) if line.strip().endswith(";")]


def oracle(seed_lines, variant_lines):
    """Both sides must compile; seed prints 1 and variant prints 2."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "seed.c").write_text("\n".join(seed_lines) + "\n")
        (tmp / "variant.c").write_text("\n".join(variant_lines) + "\n")
        for name, expected in (("seed", "1"), ("variant", "2")):
            build = subprocess.run(
                ["gcc", "-std=c11", "-O2", f"{name}.c", "-o", name],
                cwd=tmp,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if build.returncode:
                return False
            run = subprocess.run(
                [f"./{name}"], cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if run.returncode or run.stdout.strip() != expected:
                return False
    return True


def changed_statement_count(a, b):
    a = [x.strip() for x in a if x.strip().endswith(";")]
    b = [x.strip() for x in b if x.strip().endswith(";")]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")


def reduce_pair(seed, variant):
    seed = list(seed)
    variant = list(variant)
    calls = 1
    assert oracle(seed, variant)

    changed = True
    while changed:
        changed = False

        # Difference first: remove variant-only statements if both properties survive.
        seed_statements = {line.strip() for line in seed if line.strip().endswith(";")}
        for i in reversed(statement_candidates(variant)):
            if variant[i].strip() in seed_statements:
                continue
            candidate = variant[:i] + variant[i + 1 :]
            calls += 1
            if oracle(seed, candidate):
                variant = candidate
                changed = True

        # Commonality: remove the same common statement from both sides.
        variant_statements = {line.strip() for line in variant if line.strip().endswith(";")}
        common = [
            line.strip()
            for line in seed
            if line.strip().endswith(";") and line.strip() in variant_statements
        ]
        for statement in common:
            si = next((i for i, line in enumerate(seed) if line.strip() == statement), None)
            vi = next((i for i, line in enumerate(variant) if line.strip() == statement), None)
            if si is None or vi is None:
                continue
            candidate_seed = seed[:si] + seed[si + 1 :]
            candidate_variant = variant[:vi] + variant[vi + 1 :]
            calls += 1
            if oracle(candidate_seed, candidate_variant):
                seed, variant = candidate_seed, candidate_variant
                changed = True

    return seed, variant, calls


def main():
    initial = {
        "seed_tokens": token_count(SEED),
        "variant_tokens": token_count(VARIANT),
        "diff_statements": changed_statement_count(SEED, VARIANT),
    }
    seed, variant, calls = reduce_pair(SEED, VARIANT)
    result = {
        "level": "scoped L2 mechanism",
        "initial": initial,
        "reduced": {
            "seed_tokens": token_count(seed),
            "variant_tokens": token_count(variant),
            "diff_statements": changed_statement_count(seed, variant),
            "oracle_calls": calls,
        },
    }
    assert result["reduced"]["diff_statements"] == 1
    assert oracle(seed, variant)

    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (results / "reduced_seed.c").write_text("\n".join(seed) + "\n")
    (results / "reduced_variant.c").write_text("\n".join(variant) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

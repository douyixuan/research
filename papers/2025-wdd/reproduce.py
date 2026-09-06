#!/usr/bin/env python3
"""Reproduce selected WDD claims and run a fresh minimal weight-aware ddmin probe.

Levels:
  L1: reprocess released WDD CSV results for deterministic RQ2 (Wddmin vs ddmin).
  L2-scoped: run ddmin and a paper-faithful weighted-partition variant against a
  fresh compile+execute C property checker. This validates the mechanism only;
  it is not the paper's 62-benchmark experiment.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
import urllib.request
from collections import OrderedDict
from pathlib import Path

UPSTREAM_REPO = "weightdd/WeightDD"
UPSTREAM_COMMIT = "4a6cdd00f3f136867f23f76057a7104961c2e8e4"
RAW = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_COMMIT}/results_csv"
FIELDS = ["Subject", "Query", "Time", "Token_remaining"]

RQ2_FILES = {
    "hdd_ddmin_c": "hdd_ddmin_c.csv", "hdd_wdd_c": "hdd_wdd_c.csv",
    "perses_ddmin_c": "perses_ddmin_c.csv", "perses_wdd_c": "perses_wdd_c.csv",
    "hdd_ddmin_xml": "hdd_ddmin_xml.csv", "hdd_wdd_xml": "hdd_wdd_xml.csv",
    "perses_ddmin_xml": "perses_ddmin_xml.csv", "perses_wdd_xml": "perses_wdd_xml.csv",
}
EXPECTED_TABLE = {
    "hdd_ddmin_c": {"time": 39108.0, "size": 518.0}, "hdd_wdd_c": {"time": 18022.0, "size": 477.0},
    "perses_ddmin_c": {"time": 4582.0, "size": 281.0}, "perses_wdd_c": {"time": 4169.0, "size": 278.0},
    "hdd_ddmin_xml": {"time": 3152.0, "size": 98.0}, "hdd_wdd_xml": {"time": 2621.0, "size": 82.0},
    "perses_ddmin_xml": {"time": 1295.0, "size": 37.6}, "perses_wdd_xml": {"time": 1273.0, "size": 37.5},
}
PAPER_ABSTRACT = {"hdd_time_improvement_pct": 51.31, "hdd_size_improvement_pct": 9.12,
                  "perses_time_improvement_pct": 7.47, "perses_size_improvement_pct": 0.96}


def fetch_csv(name: str) -> list[dict[str, str]]:
    url = f"{RAW}/{RQ2_FILES[name]}"
    with urllib.request.urlopen(url, timeout=30) as r:
        text = r.read().decode("utf-8-sig")
    # The release mixes headered C CSVs, headerless XML CSVs, and XML files
    # with a header appended at EOF. Parse explicit fields and filter headers
    # wherever they occur.
    rows = list(csv.DictReader(text.splitlines(), fieldnames=FIELDS))
    return [row for row in rows if row["Time"].strip() != "Time"]


def dedupe_keep_last(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    by_subject: OrderedDict[str, dict[str, str]] = OrderedDict()
    duplicates: list[str] = []
    for row in rows:
        subject = row["Subject"]
        if subject in by_subject:
            duplicates.append(subject)
        by_subject[subject] = row
    return list(by_subject.values()), duplicates


def mean(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(r[key]) for r in rows) / len(rows)


def pct_improvement(base: float, weighted: float) -> float:
    return 100.0 * (base - weighted) / base


def summarize_rq2() -> dict:
    summaries: dict[str, dict] = {}
    normalized: dict[str, dict[str, dict[str, str]]] = {}
    for name in RQ2_FILES:
        raw_rows = fetch_csv(name)
        rows, duplicates = dedupe_keep_last(raw_rows)
        normalized[name] = {r["Subject"]: r for r in rows}
        summaries[name] = {"raw_rows": len(raw_rows), "unique_subjects": len(rows), "duplicates": duplicates,
                           "mean_time_s": mean(rows, "Time"), "mean_tokens_remaining": mean(rows, "Token_remaining")}

    table_checks = {}
    for name, expected in EXPECTED_TABLE.items():
        got_t, got_s = summaries[name]["mean_time_s"], summaries[name]["mean_tokens_remaining"]
        t_ok = abs(round(got_t) - expected["time"]) <= 1.0
        s_ok = abs((round(got_s, 1) if expected["size"] % 1 else round(got_s)) - expected["size"]) <= 0.1
        table_checks[name] = {"time_ok": t_ok, "size_ok": s_ok,
                              "expected_time_s": expected["time"], "expected_size": expected["size"]}
    matched = sum(v["time_ok"] and v["size_ok"] for v in table_checks.values())
    # Preserve small released-data drift as evidence rather than hiding it. At
    # least seven of the eight README aggregate rows must still reproduce.
    if matched < 7:
        raise AssertionError(f"too much released RQ2 summary drift: {table_checks}")

    per_subject = {}
    for system in ("hdd", "perses"):
        time_deltas, size_deltas = [], []
        for lang in ("c", "xml"):
            b, w = normalized[f"{system}_ddmin_{lang}"], normalized[f"{system}_wdd_{lang}"]
            for subject in sorted(set(b) & set(w)):
                time_deltas.append(pct_improvement(float(b[subject]["Time"]), float(w[subject]["Time"])))
                size_deltas.append(pct_improvement(float(b[subject]["Token_remaining"]), float(w[subject]["Token_remaining"])))
        per_subject[system] = {"subjects": len(time_deltas),
                               "mean_time_improvement_pct": sum(time_deltas) / len(time_deltas),
                               "mean_size_improvement_pct": sum(size_deltas) / len(size_deltas)}
    return {"level": "L1-partial-RQ2", "upstream_commit": UPSTREAM_COMMIT, "summaries": summaries,
            "table_checks": table_checks, "matched_readme_rows": matched,
            "per_subject_improvements": per_subject, "paper_abstract": PAPER_ABSTRACT}


RELATIVE_BODY = [1, 5, 21, 5, 21, 1, 34, 5, 55, 1, 21, 8, 2, 8, 8, 1]
CRITICAL = {3, 4, 8}
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||[-+*/%(){};,=<>]")


def fragment(i: int, scale: int) -> str:
    pads = " + 0" * scale
    value = {3: 10, 4: 12, 8: 20}.get(i, i)
    return f"static int f{i}(void) {{ return {value}{pads}; }}\n"


def token_weight(src: str) -> int:
    return len(TOKEN_RE.findall(src))


def assemble(indices: list[int], fragments: dict[int, str]) -> str:
    return "#include <stdio.h>\n" + "".join(fragments[i] for i in indices) + \
        "int main(void) { int x = f3() + f4() + f8(); printf(\"%d\\n\", x); return x == 42 ? 0 : 1; }\n"


class CompileRunOracle:
    def __init__(self, fragments: dict[int, str]):
        self.fragments, self.queries = fragments, 0

    def __call__(self, indices: list[int]) -> bool:
        self.queries += 1
        with tempfile.TemporaryDirectory(prefix="wdd-") as td:
            td = Path(td); src, exe = td / "case.c", td / "case"
            src.write_text(assemble(indices, self.fragments))
            cc = subprocess.run(["gcc", "-std=c11", "-O0", str(src), "-o", str(exe)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if cc.returncode != 0:
                return False
            run = subprocess.run([str(exe)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return run.returncode == 0 and run.stdout.strip() == "42"


def equal_partition(items: list[int], n: int) -> list[list[int]]:
    out, k = [], len(items)
    for i in range(n):
        a, b = round(i * k / n), round((i + 1) * k / n)
        if a < b: out.append(items[a:b])
    return out


def weighted_partition(items: list[int], n: int, weights: dict[int, int]) -> list[list[int]]:
    if n <= 1: return [items[:]]
    remaining_total, remaining_parts, out, cur, acc = sum(weights[x] for x in items), n, [], [], 0
    for x in items:
        target, wx = remaining_total / remaining_parts, weights[x]
        if cur and remaining_parts > 1 and abs(acc - target) <= abs((acc + wx) - target):
            out.append(cur); remaining_total -= acc; remaining_parts -= 1; cur, acc = [], 0
        cur.append(x); acc += wx
    if cur: out.append(cur)
    return out


def reduce_ddmin(items: list[int], oracle: CompileRunOracle, weights: dict[int, int] | None) -> list[int]:
    current, n = items[:], 2
    while len(current) >= 2:
        parts = weighted_partition(current, n, weights) if weights is not None else equal_partition(current, n)
        reduced = False
        for part in parts:
            removed = set(part); candidate = [x for x in current if x not in removed]
            if oracle(candidate):
                current, n, reduced = candidate, max(n - 1, 2), True; break
        if reduced: continue
        if n >= len(current): break
        n = min(len(current), n * 2)
    changed = True
    while changed:
        changed = False
        for x in current[:]:
            candidate = [y for y in current if y != x]
            if oracle(candidate): current, changed = candidate, True; break
    return current


def run_l2() -> dict:
    fragments = {i: fragment(i, RELATIVE_BODY[i]) for i in range(len(RELATIVE_BODY))}
    weights, initial = {i: token_weight(fragments[i]) for i in fragments}, list(fragments)
    plain_oracle = CompileRunOracle(fragments); plain = reduce_ddmin(initial, plain_oracle, None)
    weighted_oracle = CompileRunOracle(fragments); weighted = reduce_ddmin(initial, weighted_oracle, weights)
    if set(plain) != CRITICAL or set(weighted) != CRITICAL:
        raise AssertionError(f"unexpected minima: ddmin={plain}, Wddmin={weighted}")
    if not weighted_oracle(weighted): raise AssertionError("weighted final candidate does not satisfy compile+run property")
    return {"level": "scoped-L2-mechanism",
            "property": "gcc -std=c11 -O0 succeeds and executable prints 42/exits 0",
            "initial_fragments": len(initial), "critical_fragments": sorted(CRITICAL), "weights": weights,
            "ddmin": {"final": plain, "queries": plain_oracle.queries},
            "wddmin": {"final": weighted, "queries": weighted_oracle.queries},
            "query_improvement_pct": pct_improvement(plain_oracle.queries, weighted_oracle.queries),
            "scope_note": "Fresh compile+execute mechanism validation only; not Perses/HDD and not the 62-paper benchmark suite."}


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "results"; out_dir.mkdir(parents=True, exist_ok=True)
    report = {"rq2_l1": summarize_rq2(), "fresh_l2": run_l2()}
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    l1, l2 = report["rq2_l1"], report["fresh_l2"]
    print("\nWDD reproduction summary")
    print(f"L1 RQ2: 8 released CSVs reprocessed at {UPSTREAM_COMMIT[:12]}; README rows matched={l1['matched_readme_rows']}/8")
    print(f"Artifact duplicate rows: {l1['summaries']['hdd_ddmin_c']['duplicates']}")
    print(f"Fresh scoped L2: ddmin queries={l2['ddmin']['queries']}, Wddmin queries={l2['wddmin']['queries']}, improvement={l2['query_improvement_pct']:.2f}%")


if __name__ == "__main__":
    main()

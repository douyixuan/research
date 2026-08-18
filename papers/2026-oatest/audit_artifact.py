#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

EXPECTED = {
    "bugs_total": 56,
    "tvm_bugs": 40,
    "onnxruntime_bugs": 16,
    "fixed": 24,
    "confirmed": 18,
    "awaiting": 14,
    "confirmed_or_fixed": 42,
    "tvm_optimizations": 65,
    "onnxruntime_optimizations": 46,
    "tvm_patterns_paper": 942,
    "onnxruntime_patterns_paper": 2116,
}


def parse_bug_table(readme: str):
    rows = []
    for raw in readme.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        rows.append({
            "id": int(cells[0]),
            "compiler": cells[1],
            "symptom": cells[2],
            "root_cause": cells[3],
            "optimization": cells[4],
            "issue": cells[5],
            "status": cells[6],
        })
    return rows


def count_dirs(path: Path):
    return sum(1 for p in path.iterdir() if p.is_dir()) if path.exists() else 0


def count_files(path: Path):
    return sum(1 for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact", type=Path)
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()

    readme = (args.artifact / "readme.md").read_text(encoding="utf-8")
    rows = parse_bug_table(readme)
    compiler = Counter(r["compiler"] for r in rows)
    status = Counter(r["status"] for r in rows)
    symptom = Counter(r["symptom"] for r in rows)

    tvm_opt_dirs = count_dirs(args.artifact / "res" / "tvm_ut")
    ort_opt_dirs = count_dirs(args.artifact / "res" / "onnx_ut")
    tvm_files = count_files(args.artifact / "res" / "tvm_ut")
    ort_files = count_files(args.artifact / "res" / "onnx_ut")

    observed = {
        "bugs_total": len(rows),
        "tvm_bugs": compiler.get("TVM", 0),
        "onnxruntime_bugs": compiler.get("ONNXRuntime", 0),
        "fixed": status.get("Fixed", 0),
        "confirmed": status.get("Confirmed", 0),
        "awaiting": status.get("Awaiting", 0),
        "confirmed_or_fixed": status.get("Fixed", 0) + status.get("Confirmed", 0),
        "tvm_optimizations": tvm_opt_dirs,
        "onnxruntime_optimizations": ort_opt_dirs,
        "tvm_released_pattern_files": tvm_files,
        "onnxruntime_released_pattern_files": ort_files,
        "symptoms": dict(symptom),
        "statuses": dict(status),
    }

    checks = {
        key: observed[key] == expected
        for key, expected in EXPECTED.items()
        if key in observed
    }
    checks["bug_ids_are_1_to_56"] = sorted(r["id"] for r in rows) == list(range(1, 57))

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {"expected": EXPECTED, "observed": observed, "checks": checks}
    (args.out / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    md = [
        "# OATest released-artifact audit",
        "",
        "This is an L1 reprocessing check: it recomputes paper-level claims from the authors' released artifact. It is not a fresh fuzzing campaign.",
        "",
        "## Bug corpus",
        "",
        f"- total rows: **{len(rows)}** (paper: 56)",
        f"- TVM / ONNXRuntime: **{compiler.get('TVM', 0)} / {compiler.get('ONNXRuntime', 0)}** (paper: 40 / 16)",
        f"- Fixed / Confirmed / Awaiting: **{status.get('Fixed', 0)} / {status.get('Confirmed', 0)} / {status.get('Awaiting', 0)}**",
        f"- Confirmed-or-fixed: **{status.get('Fixed', 0) + status.get('Confirmed', 0)}** (paper: 42; fixed subset: 24)",
        f"- Symptoms: `{dict(symptom)}`",
        "",
        "## Released pattern corpus structure",
        "",
        f"- TVM optimization directories: **{tvm_opt_dirs}** (paper: 65 optimizations)",
        f"- ONNXRuntime optimization directories: **{ort_opt_dirs}** (paper: 46 optimizations)",
        f"- Recursive files under `res/tvm_ut`: **{tvm_files}**; paper reports 942 extracted TVM patterns.",
        f"- Recursive files under `res/onnx_ut`: **{ort_files}**; paper reports 2,116 extracted ONNXRuntime patterns.",
        "",
        "The recursive file counts are reported rather than asserted equal to the pattern counts because the repository layout is released data, not an explicit one-file-per-final-pattern contract.",
        "",
        "## Checks",
        "",
    ]
    for key, ok in checks.items():
        md.append(f"- {'PASS' if ok else 'FAIL'} `{key}`")
    (args.out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    hard = [
        "bugs_total", "tvm_bugs", "onnxruntime_bugs", "fixed", "confirmed",
        "awaiting", "confirmed_or_fixed", "tvm_optimizations",
        "onnxruntime_optimizations", "bug_ids_are_1_to_56",
    ]
    failed = [k for k in hard if not checks.get(k, False)]
    if failed:
        raise SystemExit("hard checks failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

PAPER = {
    "bugs_total": 56,
    "tvm_bugs": 40,
    "onnxruntime_bugs": 16,
    "fixed": 24,
    "confirmed": 18,
    "awaiting": 14,
    "confirmed_or_fixed": 42,
    "tvm_optimizations": 65,
    "onnxruntime_optimizations": 46,
    "tvm_patterns": 942,
    "onnxruntime_patterns": 2116,
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


def top_level_dirs(path: Path):
    return sorted(p.name for p in path.iterdir() if p.is_dir()) if path.exists() else []


def files(path: Path):
    return [p for p in path.rglob("*") if p.is_file()] if path.exists() else []


def suffix_counts(paths):
    c = Counter((p.suffix.lower() or "<none>") for p in paths)
    return dict(sorted(c.items()))


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

    tvm_dirs = top_level_dirs(args.artifact / "res" / "tvm_ut")
    ort_dirs = top_level_dirs(args.artifact / "res" / "onnx_ut")
    tvm_files = files(args.artifact / "res" / "tvm_ut")
    ort_files = files(args.artifact / "res" / "onnx_ut")

    observed = {
        "bugs_total": len(rows),
        "tvm_bugs": compiler.get("TVM", 0),
        "onnxruntime_bugs": compiler.get("ONNXRuntime", 0),
        "fixed": status.get("Fixed", 0),
        "confirmed": status.get("Confirmed", 0),
        "awaiting": status.get("Awaiting", 0),
        "confirmed_or_fixed": status.get("Fixed", 0) + status.get("Confirmed", 0),
        "tvm_pattern_buckets": len(tvm_dirs),
        "onnxruntime_pattern_buckets": len(ort_dirs),
        "tvm_released_files": len(tvm_files),
        "onnxruntime_released_files": len(ort_files),
        "tvm_suffixes": suffix_counts(tvm_files),
        "onnxruntime_suffixes": suffix_counts(ort_files),
        "symptoms": dict(symptom),
        "statuses": dict(status),
    }

    # Hard L1 checks are claims for which the released artifact has an unambiguous
    # representation. A directory bucket is not assumed to equal one compiler pass.
    checks = {
        "bugs_total": observed["bugs_total"] == PAPER["bugs_total"],
        "tvm_bugs": observed["tvm_bugs"] == PAPER["tvm_bugs"],
        "onnxruntime_bugs": observed["onnxruntime_bugs"] == PAPER["onnxruntime_bugs"],
        "fixed": observed["fixed"] == PAPER["fixed"],
        "confirmed": observed["confirmed"] == PAPER["confirmed"],
        "awaiting": observed["awaiting"] == PAPER["awaiting"],
        "confirmed_or_fixed": observed["confirmed_or_fixed"] == PAPER["confirmed_or_fixed"],
        "bug_ids_are_1_to_56": sorted(r["id"] for r in rows) == list(range(1, 57)),
        "tvm_released_files_equal_reported_patterns": len(tvm_files) == PAPER["tvm_patterns"],
    }

    discrepancies = {
        "tvm_pattern_buckets_vs_reported_optimizations": {
            "artifact_buckets": len(tvm_dirs),
            "paper_optimizations": PAPER["tvm_optimizations"],
            "delta": len(tvm_dirs) - PAPER["tvm_optimizations"],
            "interpretation": "Top-level artifact directories are pattern buckets and are not a documented one-to-one encoding of compiler optimizations.",
        },
        "onnxruntime_released_files_vs_reported_patterns": {
            "artifact_files": len(ort_files),
            "paper_patterns": PAPER["onnxruntime_patterns"],
            "delta": len(ort_files) - PAPER["onnxruntime_patterns"],
            "interpretation": "The released corpus contains more files than the final paper's reported extracted-pattern count; preserve this as an artifact/paper snapshot discrepancy rather than silently normalizing it.",
        },
    }

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {
        "paper_claims": PAPER,
        "observed": observed,
        "hard_checks": checks,
        "structural_discrepancies": discrepancies,
    }
    (args.out / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    md = [
        "# OATest released-artifact audit",
        "",
        "This is an L1 reprocessing check: it recomputes unambiguous paper-level claims from the authors' released artifact. It is not a fresh fuzzing campaign.",
        "",
        "## Bug corpus",
        "",
        f"- total rows: **{len(rows)}** (final paper: 56)",
        f"- TVM / ONNXRuntime: **{compiler.get('TVM', 0)} / {compiler.get('ONNXRuntime', 0)}** (final paper: 40 / 16)",
        f"- Fixed / Confirmed / Awaiting: **{status.get('Fixed', 0)} / {status.get('Confirmed', 0)} / {status.get('Awaiting', 0)}**",
        f"- Confirmed-or-fixed: **{status.get('Fixed', 0) + status.get('Confirmed', 0)}** (final paper: 42; fixed subset: 24)",
        f"- Symptoms: `{dict(symptom)}`",
        "",
        "## Released corpus structure",
        "",
        f"- TVM top-level pattern buckets: **{len(tvm_dirs)}**; final paper reports **65 optimizations**.",
        f"- TVM recursive released files: **{len(tvm_files)}**; final paper reports **942 patterns**.",
        f"- TVM suffixes: `{suffix_counts(tvm_files)}`",
        f"- ONNXRuntime top-level pattern buckets: **{len(ort_dirs)}**; final paper reports **46 optimizations**.",
        f"- ONNXRuntime recursive released files: **{len(ort_files)}**; final paper reports **2,116 patterns**.",
        f"- ONNXRuntime suffixes: `{suffix_counts(ort_files)}`",
        "",
        "Important: an artifact directory bucket is not assumed to be a one-to-one encoding of an optimization pass. The ONNXRuntime file-count difference is preserved as a reproducibility finding rather than forced to match the paper.",
        "",
        "## Hard checks",
        "",
    ]
    for key, ok in checks.items():
        md.append(f"- {'PASS' if ok else 'FAIL'} `{key}`")
    md += [
        "",
        "## Structural discrepancies to investigate",
        "",
        f"- TVM: **{len(tvm_dirs)} artifact buckets vs 65 reported optimizations**.",
        f"- ONNXRuntime: **{len(ort_files)} released files vs 2,116 reported patterns** (delta {len(ort_files) - PAPER['onnxruntime_patterns']:+d}).",
        "",
        "These do not invalidate the bug-table L1 reproduction; they show that artifact layout is not identical to the paper's conceptual/counting units and should be pinned/versioned explicitly.",
    ]
    (args.out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("hard checks failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()

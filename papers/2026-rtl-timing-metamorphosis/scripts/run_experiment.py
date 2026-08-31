#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def run(cmd, log_name):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    (RESULTS / log_name).write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise SystemExit(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p.stdout.strip()


run(["python3", "scripts/metamorphose.py"], "metamorphose.log")

# Exhaustive simulation over all 2^3 input vectors.
tb = RESULTS / "tb_equiv.sv"
tb.write_text(r'''module tb;
  reg a, b, c;
  wire y_org, y_mut;
  integer i;
  logic_original org(.a(a), .b(b), .c(c), .y(y_org));
  logic_mutant mut(.a(a), .b(b), .c(c), .y(y_mut));
  initial begin
    for (i = 0; i < 8; i = i + 1) begin
      {a,b,c} = i[2:0];
      #1;
      if (y_org !== y_mut) begin
        $display("FAIL vector=%0d org=%b mut=%b", i, y_org, y_mut);
        $fatal(1);
      end
    end
    $display("PASS 8/8 vectors equivalent");
    $finish;
  end
endmodule
''')
run([
    "iverilog", "-g2012", "-o", str(RESULTS / "equiv.vvp"),
    str(RTL / "logic_original.v"), str(RTL / "logic_mutant.v"), str(tb)
], "iverilog_compile.log")
sim_out = run(["vvp", str(RESULTS / "equiv.vvp")], "iverilog_run.log")
if "PASS 8/8 vectors equivalent" not in sim_out:
    raise SystemExit("simulation did not report exhaustive equivalence")

# Formal equivalence with Yosys' equivalence machinery.
yosys_equiv = """
read_verilog rtl/logic_original.v rtl/logic_mutant.v
proc
memory
opt
equiv_make logic_original logic_mutant equiv
hierarchy -top equiv
equiv_simple
equiv_status -assert
"""
run(["yosys", "-p", yosys_equiv], "yosys_equiv.log")


def synth(label, source, top):
    out_json = RESULTS / f"{label}.json"
    script = f"read_verilog {source}; synth -top {top}; write_json {out_json}"
    run(["yosys", "-p", script], f"yosys_{label}.log")
    data = json.loads(out_json.read_text())
    modules = data["modules"]
    module = modules.get(top) or modules.get("\\" + top)
    if module is None:
        raise SystemExit(f"top module {top} missing from {out_json}")
    netnames = module.get("netnames", {})
    return {
        "cells": len(module.get("cells", {})),
        "netnames": len(netnames),
        "wire_bits": sum(len(v.get("bits", [])) for v in netnames.values()),
    }


org = synth("original_synth", "rtl/logic_original.v", "logic_original")
mut = synth("mutant_synth", "rtl/logic_mutant.v", "logic_mutant")

def ratio(a, b):
    return None if b == 0 else round(a / b, 4)

summary = {
    "reproduction_level": "L0 + scoped L2",
    "scope": "logic-operation metamorphosis only; no LLM campaign and no paper benchmark artifact",
    "paper_public_v1_benchmark_cases": {
        "logic_operation": 54,
        "data_path": 27,
        "timing_control_flow": 40,
        "clock_domain": 32,
        "total": 153,
    },
    "fresh_checks": {
        "simulation_vectors": 8,
        "simulation_equivalent": True,
        "yosys_formal_equivalent": True,
    },
    "current_yosys_structural_proxy": {
        "original": org,
        "mutant": mut,
        "mutant_over_original": {
            "cells": ratio(mut["cells"], org["cells"]),
            "netnames": ratio(mut["netnames"], org["netnames"]),
            "wire_bits": ratio(mut["wire_bits"], org["wire_bits"]),
        },
        "warning": "JSON netname/cell counts are a scoped structural proxy, not the paper's full PPA measurement pipeline.",
    },
    "tool_versions": {
        "yosys": run(["yosys", "-V"], "yosys_version.log"),
        "iverilog": run(["iverilog", "-V"], "iverilog_version.log").splitlines()[0],
    },
}
(RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))

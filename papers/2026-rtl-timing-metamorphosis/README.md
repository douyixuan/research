# Rethinking LLM-aided RTL Code Optimization Via Timing Logic Metamorphosis

## Status

**Current level: L0 artifact/provenance audit + scoped L2 live-minimal.**

This is deliberately **not** labeled L1 or L3. The public sources currently do not expose the final TRETS benchmark/artifact/raw outputs needed to recompute the paper tables, and the public arXiv v1 predates the 2026 TRETS authorship/version listed by Yongqiang Tian's publication page.

## Paper identity and provenance

- Yongqiang Tian publication page: lists **TRETS 2026**, title `Rethinking LLM-aided RTL Code Optimization Via Timing Logic Metamorphosis`, authors Zhihao Xu, Bixin Li, Ran Yan, Lulu Wang, Yongqiang Tian.
- Public arXiv v1: `arXiv:2507.16808`, submitted 2025-07-22, title uses `LLM-Based`, and lists Zhihao Xu, Bixin Li, Lulu Wang.
- Zhihao Xu's public page still describes the manuscript as a 2025 TRETS submission and includes Ran Yan but not Yongqiang Tian.
- Exact-title GitHub repository search did not surface an official public artifact during the 2026-08-31 sweep.

Because those public snapshots disagree, this directory treats the arXiv v1 as the only fully inspectable technical specification and records the TRETS 2026 metadata separately rather than silently merging them.

Sources:
- https://yqtian.com/pub.html
- https://arxiv.org/abs/2507.16808
- https://arxiv.org/html/2507.16808
- https://zhihaoxu1325.github.io/

## Core insight

The paper evaluates RTL optimizers with **metamorphic robustness**, not just single-input PPA. Start from an RTL design, construct a semantically equivalent but structurally harder mutant, optimize both, and ask whether optimization quality remains stable. The four categories are logic operations, data paths, timing-control flow, and clock domains.

The public v1 reports a benchmark of 54 + 27 + 40 + 32 = **153 RTL cases**. It checks semantic equivalence with formal verification and Icarus Verilog simulation, then compares wires, cells, area, delay, and power after optimization/synthesis.

The paper's main qualitative result is asymmetric: LLM-based optimizers are strong on logic/data-path rewrites but degrade on timing-control and clock-domain mutations. For example, the public v1 reports Yosys mutant logic-operation wire/cell ratios of **4.67× / 3.25×**, while timing-control and clock-domain experiments expose broader trade-offs among delay, area, and power.

## What this reproduction actually runs

The deterministic lane implements one fresh end-to-end instance of the paper's **logic-operation metamorphosis**:

1. start from `(a & b) | (a & c)`;
2. generate a Boolean-equivalent De-Morgan-expanded mutant plus a redundant `a & b & c` term;
3. exhaustively simulate all 8 input vectors with Icarus Verilog;
4. run a formal equivalence check with Yosys;
5. synthesize original and mutant with the currently available Yosys;
6. record structural JSON proxies (`cells`, `netnames`, `wire_bits`) and tool versions.

Run locally:

```bash
sudo apt-get install yosys iverilog
./reproduce.sh
```

Outputs are written to `results/`. CI uploads that directory as an artifact.

## Paper vs reproduction

| Item | Paper/public v1 | This run |
|---|---|---|
| Benchmark | 153 cases across 4 categories | 1 logic-operation pair |
| Semantic checking | formal verification + Icarus | Yosys formal equivalence + exhaustive Icarus |
| Optimizers | RTLRewriter, GPT-4, Claude-3.7-Sonnet, Yosys | Yosys only |
| Metrics | wires, cells, area, delay, power | Yosys JSON structural proxies only |
| Model calls | yes | none |
| Level | full empirical study | **scoped L2**, not L1/L3 |

`results/summary.json` is generated from the live toolchain and is the evidence source for the scoped L2 result.

## Experiment design

### Hypothesis H1 — semantic preservation

The generated mutant must be functionally equivalent to the original for all Boolean inputs. Failure in either exhaustive simulation or formal equivalence fails CI.

### Hypothesis H2 — optimization robustness probe

After synthesis, compare mutant/original structural proxies. This is a **modern-toolchain drift probe**, not a reproduction of the paper's aggregate PPA ratios. If current Yosys canonicalizes this small mutant completely, that is useful evidence that the paper's benchmark-level degradation depends on harder cases and/or the exact Yosys flow/version.

### Promotion path

- **To L1:** obtain the final TRETS artifact/raw metric files, pin the exact revision, and recompute all reported aggregate tables/figures.
- **To L2 broader:** run representative logic, data-path, FSM, and CDC mutants with the same formal/simulation guard.
- **To L3:** recover all 153 cases, exact optimizer versions/prompts, synthesis/PPA environment, and repeated LLM runs.
- **To L4:** add model/toolchain-drift and fairness-controlled experiments below.

## Threats and limitations

1. **Version/provenance drift.** The inspectable arXiv v1 and the 2026 author-page record disagree on title/year/authors.
2. **No final artifact found.** Benchmark files, raw outputs, exact prompts, model snapshots, and final TRETS result package are unavailable in the sources checked here.
3. **Metric mismatch.** JSON structural counts are not equivalent to the paper's complete area/delay/power flow.
4. **Tiny scope.** One combinational mutant cannot establish conclusions about FSMs or clock-domain logic.
5. **Model drift.** `GPT-4` and `Claude-3.7-Sonnet` labels are not enough to reconstruct exact hosted model snapshots later.
6. **Toolchain drift.** Yosys/ABC/Icarus behavior can change materially across releases.

## Research extensions

The most valuable L4 is a **versioned robustness matrix**:

`{Yosys releases, RTLRewriter, current LLMs} × {original, metamorphic mutant} × {logic, datapath, FSM, CDC}`

For every generated rewrite, first prove behavioral equivalence, then compare PPA under a fixed synthesis backend and fixed budget. Record model tokens/cost/latency and repeat stochastic models enough times to report variance.

Two especially useful ablations:

- **Temporal-context ablation:** source-only prompt vs source + explicit cycle/clock-domain contract vs source + extracted state-transition graph.
- **Fair baseline ablation:** give compiler/EDA baselines equivalent canonicalization opportunities before attributing improvements to semantic reasoning.

For compiler work more broadly, the same idea maps naturally to LLVM/MLIR: build semantics-preserving IR metamorphoses, then measure whether an optimizer or LLM-assisted pass remains invariant in code quality across equivalent but structurally harder IR.

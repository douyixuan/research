# Bounded Exhaustive Random Program Generation for Testing Solidity Compilers

**Paper:** Haoyang Ma, Alastair F. Donaldson, Qingchao Shen, Yongqiang Tian, Junjie Chen, Shing-Chi Cheung. ICSE 2026.

- Paper: https://www.doc.ic.ac.uk/~afd/papers/2026/ICSE.pdf
- arXiv: https://arxiv.org/abs/2503.20332
- Official implementation: https://github.com/haoyang9804/Erwin
- Paper-version upstream commit used here: `c4f99a37d3f22cd6bd41a531a59c0e64ab39a3aa`
- Package at that commit: `@__haoyang__/erwin` 1.3.1
- Evidence for the pin: its child commit `6bd23681...` is explicitly "publish 1.3.2" and changes `package.json` from 1.3.1 to 1.3.2.

## Core insight

Traditional random program generators spend most of their budget wandering through a huge language search space. Erwin instead separates generation into two stages:

1. generate a type/location/scope-agnostic Solidity program template;
2. enumerate valid assignments for bug-relevant qualifiers under constraints, up to a configurable bound.

The research hypothesis is not simply "more programs is better". It is that **systematically exploiting a bug-relevant local subspace around each randomly generated template is a better use of testing budget than immediately abandoning the template after the first valid instantiation**.

The comparison against `SoliditySmith` is the cleanest ablation: SoliditySmith is essentially Erwin in `gen1` mode, stopping after the first valid substitution.

## Paper claims / research questions

### RQ1 — effectiveness and efficiency

The final ICSE paper reports 26 bugs across `solc`, `solang`, and `slither`, plus 4,599 edges and 14,824 lines in `solc` that are not covered by its unit tests. Its throughput study varies the per-template instantiation bound from gen1 to gen300; reported test-program throughput peaks at 876.17 programs/s for gen150.

There is a reproducibility-relevant inconsistency inside the final PDF: Table 1 says **26 / 16 confirmed / 9 fixed / 3 duplicate**, while the immediately following prose says **26 / 18 confirmed / 10 fixed**, matching the current conference abstract. We therefore record both instead of silently choosing one.

The older arXiv abstract also reflects an earlier snapshot: **23 previously unknown bugs** and **4,582 edges / 14,737 lines** missed by unit tests, rather than the final conference version's 26 total bugs and 4,599 / 14,824 coverage numbers. This is useful evidence that paper/artifact snapshots must be pinned when comparing results.

### RQ2 — comparison with Solidity fuzzers

Over a 20-day comparison on the historical compiler-bug dataset, the paper reports:

- Erwin finds 18 bugs;
- 16 are missed by ACF and Fuzzol;
- Erwin covers 4,622 edges and 14,828 lines missed by ACF and Fuzzol after the coverage experiment.

The paper also notes an important ceiling: Erwin lacked language features required by 72 of the 104 historical bugs, so the headline comparison is constrained by supported grammar, not only search quality.

### RQ3 — bounded exhaustiveness ablation

The main ablation compares Erwin against SoliditySmith. SoliditySmith finds 12 bugs, all also found by Erwin; Erwin finds six additional bugs. Across the selected gen settings, Erwin reports roughly 400 more edges and 480 more lines on average than SoliditySmith.

## What this repository actually reproduces

**Current level: scoped L2 — live-minimal mechanism reproduction.**

`reproduce.sh` does not claim to rerun the 20-day fuzzing campaign or the 24-hour coverage study. Instead it performs a fresh end-to-end check of the released mechanism:

1. clone the official Erwin repository at the recovered 1.3.1 paper snapshot;
2. install and build it on Node.js 20;
3. run bounded exhaustive generation for `type`, `loc`, and `scope` modes with a small bound;
4. require every qualifier mode to emit at least one Solidity program;
5. compile the generated programs with `solcjs 0.8.20`, the grammar version named by the paper, and require at least one successful compile;
6. emit a machine-readable and human-readable summary as a GitHub Actions artifact.

This is a real execution of Erwin's generation/lowering path, but it is intentionally much smaller than the paper's evaluation. It tests artifact health and the core generation mechanism, not bug-finding superiority.

## Paper vs. reproduction

| Dimension | Paper | This repo |
|---|---|---|
| Erwin version | 1.3.1 | **1.3.1, exact recovered upstream snapshot** |
| Hardware | Threadripper-class host, long campaigns | GitHub-hosted Ubuntu runner |
| Search budget | 20-day bug study; 24-hour coverage runs | one small generation round per qualifier mode |
| Targets | solc 0.8.20–0.8.28, solang 0.3.3, slither 0.10.4 | generator + `solcjs 0.8.20` validity smoke test |
| Baselines | ACF, Fuzzol, SoliditySmith | none yet |
| Evidence | bugs, edge/line coverage, throughput | generated-program count + compile pass/fail |
| Reproduction level | — | scoped L2 |

## Threats / limitations

- **Randomness:** the released CLI does not expose an obvious single random-seed flag. CI therefore verifies invariants and records counts rather than expecting bit-for-bit identical programs.
- **Compiler/runtime mismatch:** the paper tested native `solc`; this small CI lane uses `solcjs 0.8.20` to cheaply test generated-program validity. That is not a substitute for the paper's native compiler builds or SMT/model-checker configuration.
- **No historical bug campaign:** reproducing RQ2/RQ3 faithfully requires the 104-bug dataset, ACF/Fuzzol builds, historical compiler versions, multi-day execution, and coverage instrumentation.
- **Reported-count inconsistency:** Table 1 and prose disagree on confirmed/fixed bug totals. Any L1 table reconstruction should treat the underlying issue list as the source of truth and timestamp its status.
- **Paper snapshot drift:** arXiv and final ICSE numbers differ, so future comparisons should pin both paper revision and artifact revision.

## Best next experiments

### 1. Budget-normalized exploitation/exploration curve

The paper varies `-max`, but the most useful modern extension is to compare `gen1`, `genN`, and an **adaptive N** under identical CPU-seconds. Choose N online from the observed number of feasible substitutions, template novelty, and recent coverage gain. This tests whether fixed bounded exhaustiveness is actually optimal.

### 2. Version-matrix bug survival

Run every published Erwin bug trigger across:

`paper version -> latest patch in that series -> current stable -> nightly`

Record `introduced / survives / fixed / regressed`. This turns the bug list into a compiler-regression dataset rather than a static paper artifact.

### 3. Generalize the idea to compiler IRs

For LLVM/MLIR/Triton, treat a randomly generated IR skeleton as the template and make pass-sensitive attributes, types, layouts, memory spaces, vector widths, or lowering choices the holes. The key research question becomes whether bounded enumeration around a promising IR skeleton outperforms continually sampling fresh IR programs at equal compilation cost.

### 4. Better validity metric

Do not count only generated programs per second. Report:

`valid programs / CPU-second`, `new coverage edges / 1k valid programs`, `unique compiler states / CPU-second`, and `bugs / million compilations`.

This separates raw generator throughput from testing effectiveness.

## L3 plan

To move to L3:

1. use the now-recovered Erwin 1.3.1 snapshot as the generator baseline;
2. build native `solc` versions 0.8.20–0.8.28 plus solang 0.3.3 and slither 0.10.4;
3. recover the 104-bug historical dataset and baseline seed pools;
4. containerize ACF and Fuzzol;
5. run gen1/gen50/gen100/gen150/gen200/gen250/gen300 with repeated trials;
6. collect edge/line coverage using the paper-compatible instrumentation;
7. reproduce Figures 10–13 and Table 2 with confidence intervals, not only medians;
8. reconcile the 16/9 vs 18/10 confirmed/fixed discrepancy against timestamped GitHub issue state.

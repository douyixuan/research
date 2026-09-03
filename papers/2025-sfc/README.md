# SFC — Boosting Program Reduction with Syntax-Guided Transformations

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. **Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations**, PACMPL/OOPSLA 2025, DOI `10.1145/3763053`.

- Author-hosted paper: `https://cs.uwaterloo.ca/~cnsun/public/publication/oopsla25/oopsla25.pdf`
- Current upstream implementation: `uw-pluverse/perses`
- Pinned upstream commit: `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27)
- Current level: **L0 source/provenance audit + scoped L2 current-Perses mechanism**. This is **not L1** and is not a paper-scale reproduction.

## Core insight

Perses-style reducers historically rely mainly on subtree hoisting and quantified-node deletion. Those operations preserve syntax, but they prune away valid rewrites that change one grammatical form into another. The paper adds **Structure Form Conversion (SFC)** and builds three reducers on top of it:

1. Smaller Structure Replacement — choose a strictly smaller alternative grammatical form;
2. Identifier Elimination — use SFC to remove identifier uses and expose later deletion opportunities;
3. Structure Canonicalization — rewrite equal-size structures toward a canonical grammar alternative.

The paper reports that `SFC_Perses` produces outputs 36.82%, 18.71%, and 41.05% smaller than Perses on C, Rust, and SMT-LIBv2, respectively; `SFC_Vulcan` improves over Vulcan by 14.51%, 7.65%, and 7.66%. The canonicalization experiment contains 3,796 C programs / 46 unique bugs and reports 442 / 435 additional duplicate eliminations for SFC_Perses / SFC_Vulcan.

## What is actually reproduced here

The current public Perses tree now contains an `sfc/` implementation. Importantly, it also contains `PaperExampleSimplificationsTest.kt`, which explicitly encodes the **12 example SFC simplifications from §4.1** against the real C grammar, plus focused tests for the three SFC reducers.

`reproduce.sh` pins the upstream commit and freshly runs these upstream Bazel test targets with test-result caching disabled:

- `PaperExampleSimplificationsTest` — the 12 paper examples;
- `StructureFormConverterCTest` — SFC candidate generation on the C grammar;
- `SmallerStructureReplacementReducerTest`;
- `IdentifierUseEliminationReducerTest`;
- `StructureCanonicalizationReducerTest`.

This exercises the authors' current implementation rather than a local reimplementation. It validates the mechanism and reducer invariants on a fresh checkout, hence **scoped L2 mechanism**. It does not regenerate the 245 minimization benchmarks or the 3,796-program canonicalization study.

## Run

```bash
bash papers/2025-sfc/reproduce.sh
```

Requires network access, Git, and Bazel/Bazelisk. The GitHub Action installs Bazelisk and uploads the fresh test log and summary.

## Paper vs reproduction

| Evidence | Paper | This repo | Level/status |
|---|---:|---:|---|
| SFC example simplifications | 12 examples in §4.1 | upstream test contains exactly 12 and is run fresh | scoped L2 mechanism |
| SFC methods | 3 | all 3 current reducer test suites run | scoped L2 mechanism |
| C reduction gain vs Perses | 36.82% | not regenerated | L3 missing |
| Rust reduction gain vs Perses | 18.71% | not regenerated | L3 missing |
| SMT-LIBv2 reduction gain vs Perses | 41.05% | not regenerated | L3 missing |
| C/Rust/SMT gain vs Vulcan | 14.51% / 7.65% / 7.66% | not regenerated | L3 missing |
| Canonicalization benchmark | 3,796 programs, 46 bugs | not regenerated | L3 missing |
| Additional duplicate eliminations | +442 / +435 | not regenerated | L3 missing |

## Experiment design for L3

A faithful paper-scale rerun should pin the paper-era SFC/Perses/Vulcan revisions, compiler/solver versions, and the exact Benchmark-Reduce/Benchmark-Cano inputs. Run single-threaded as in the paper and preserve per-case token count, property-check queries, wall time, and final reduced program. Repeat wall-time measurements to quantify variance, then recompute the paper's per-case percentage changes and Wilcoxon tests rather than only comparing means.

The largest current blocker is **paper-era artifact provenance**: the public Perses master contains the SFC implementation and paper-example tests, but this study has not located a separately versioned public package containing the exact 245 + 3,796 benchmark inputs and paper-era result files. Without those inputs/results, claiming L1 or L3 would be incorrect.

## Threats and limitations

1. **Post-paper implementation drift.** The pinned Perses commit is from 2026-08-27, after the October 2025 paper. Passing current tests does not prove the paper revision behaved identically.
2. **No L1 evidence package.** The paper's aggregate numbers are not being recomputed from author-released result files here.
3. **Mechanism scope.** The targeted tests validate SFC conversion and reducer invariants, not full benchmark-scale search behavior.
4. **Runtime sensitivity.** The paper used Ubuntu 20.04, AMD 7950X, 128 GB RAM, and one thread; GitHub-hosted runners differ substantially.
5. **Benchmark age.** Historical C/Rust/SMT bugs may favor grammar structures that motivated SFC; fresh compiler bugs are needed to test generalization.
6. **Search budget confound.** SFC intentionally trades more time for smaller results, so comparisons should be normalized by property-query or wall-clock budget.

## Most valuable extension — budget-normalized SFC on fresh compiler bugs

Use compiler bugs filed after the paper and compare Perses against SFC_Perses under equal **property-query budgets** and equal **wall-clock budgets**. Instrument every SFC proposal with transformation class, accepted/rejected result, token delta, downstream deletion unlocked, and oracle cost. Then run leave-one-method-out ablations for Smaller Structure Replacement, Identifier Elimination, and Structure Canonicalization.

This tests whether SFC's benefit survives toolchain/benchmark drift and identifies which grammatical conversions have positive reduction ROI instead of treating the three methods as one opaque bundle.

## Upgrade path

- **L1:** locate the paper-era released result tables/raw outputs and recompute published aggregates without rerunning reducers.
- **L2 stronger:** run one complete fresh bug-triggering program through baseline Perses and SFC_Perses with the same property oracle.
- **L3:** rerun Benchmark-Reduce and Benchmark-Cano at paper-like scale and compare distributions/statistics.
- **L4:** fresh post-2025 bugs + budget-normalized baselines + method-level ablation/ROI analysis.

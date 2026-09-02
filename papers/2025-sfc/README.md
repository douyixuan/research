# SFC — Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. PACMPL/OOPSLA 2025, DOI 10.1145/3763053.

- Paper page: https://doi.org/10.1145/3763053
- Official implementation used here: https://github.com/uw-pluverse/perses
- Pinned upstream commit: `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27)
- Current reproduction level: **L0 implementation audit + scoped L2 mechanism reproduction**.
- This is **not L1** and **not a paper-scale reproduction**: no paper-era raw benchmark tables/results were found in the public paper page or current Perses repository during the 2026-09-02 sweep.

## Core insight

Syntax-guided reducers such as Perses can prune too aggressively: a subtree may be replaceable by another grammar-derived form that is semantically acceptable and substantially smaller, but traditional hoisting/deletion never explores it. The paper introduces **Structure Form Conversion (SFC)** to enumerate alternative grammar structures, then uses SFC in three reducers:

1. **Smaller Structure Replacement** — replace a subtree with a smaller compatible structure form;
2. **Identifier Elimination** — use a conversion that removes an identifier use while preserving the interesting property;
3. **Structure Canonicalization** — replace an equal-size structure with a grammar-defined more canonical form.

The important systems idea is that the grammar is used not only to avoid invalid candidates, but to *generate new valid structural neighborhoods* for the reducer to search.

## Paper claims

The paper reports the following aggregate improvements over the corresponding baselines:

| Baseline | C | Rust | SMT-LIBv2 | Time cost reported |
|---|---:|---:|---:|---|
| Perses -> SFC-Perses | 36.82% smaller | 18.71% smaller | 41.05% smaller | 3.65x / 16.99x / 1.42x |
| Vulcan -> SFC-Vulcan | 14.51% smaller | 7.65% smaller | 7.66% smaller | 1.56x / 2.35x / 1.42x |

For bug deduplication, the paper additionally reports 3,796 C programs covering 46 unique bugs, with SFC-Perses and SFC-Vulcan collapsing 442 and 435 more duplicates to identical reduced programs than their baselines.

These are **paper claims only** in this directory; they are not labeled L1 because the underlying paper-era raw data are not present in the public materials found today.

## What is actually rerun

The current official Perses source contains a dedicated `sfc/` implementation and a test named `PaperExampleSimplificationsTest` whose source explicitly states that it reproduces the **twelve simplifications from Section 4.1** on the real C grammar. The same package also contains functional tests for all three SFC-based reducers.

`reproduce.sh` pins that upstream commit and executes these four official targets:

```text
//sfc/test/org/perses/reduction/reducer/sfc:PaperExampleSimplificationsTest
//sfc/test/org/perses/reduction/reducer/sfc:SmallerStructureReplacementReducerTest
//sfc/test/org/perses/reduction/reducer/sfc:IdentifierUseEliminationReducerTest
//sfc/test/org/perses/reduction/reducer/sfc:StructureCanonicalizationReducerTest
```

Passing them demonstrates a fresh, executable **scoped L2 mechanism reproduction** of the paper examples and three reduction mechanisms on the modern Perses codebase. It does not reproduce the full C/Rust/SMT benchmark study or the 3,796-program deduplication experiment.

## Run

Prerequisites: Git, Java and Bazelisk. The CI checks out the pinned upstream revision automatically.

```bash
./papers/2025-sfc/reproduce.sh
```

For an already checked-out upstream tree:

```bash
./papers/2025-sfc/reproduce.sh /path/to/perses
```

The script writes `papers/2025-sfc/results/summary.json` and per-target Bazel logs. CI uploads the entire results directory as an artifact.

## Experiment design

### H1 — paper examples remain executable

At the pinned modern Perses revision, all twelve Section 4.1 simplifications represented by the official test should pass against the production C grammar.

### H2 — all three SFC reducer families remain functional

The official functional tests for Smaller Structure Replacement, Identifier Elimination and Structure Canonicalization should all pass from a clean checkout.

### H3 — toolchain drift is visible rather than hidden

The upstream revision and Bazel version are pinned/recorded. A future toolchain retest should change one dimension at a time and compare failures against this snapshot.

## Paper vs reproduction

| Item | Paper | This reproduction |
|---|---|---|
| Languages | C, Rust, SMT-LIBv2 | C-oriented official SFC mechanism tests |
| Main reduction study | full benchmark suite | not rerun |
| Dedup study | 3,796 C programs / 46 bugs | not rerun |
| SFC examples | Section 4.1 examples | official 12-example test rerun |
| Three SFC reducer methods | evaluated in prototypes | official functional tests rerun |
| Level | — | **L0 + scoped L2** |

## Threats and limitations

- **Post-paper implementation drift:** the pinned Perses revision is from 2026-08-27, not the exact OOPSLA experiment snapshot. Passing current tests establishes that the mechanism survives, not that the original paper binaries are reproduced.
- **No L1 raw-data path found:** without the paper-era result CSV/logs and benchmark manifest, the headline percentages cannot be independently recomputed.
- **Test-selection bias:** official tests target intended behavior and may miss adversarial grammar shapes or interactions with other reducers.
- **No cost comparison:** the scoped tests do not measure the paper's substantial runtime overhead, especially the reported 16.99x Rust cost for SFC-Perses.
- **Canonicalization metric gap:** functional correctness of canonicalization is not the same as reproducing the paper's dataset-level canonicalization/deduplication gains.

## Most useful extension: transformation ROI under equal budget

A high-value L4 study is to instrument SFC at transformation granularity and compare it with Perses/Vulcan under the **same oracle-call and wall-clock budget**. Record, per SFC conversion family:

- candidates generated;
- syntactically valid candidates;
- property-test acceptance rate;
- accepted token reduction;
- oracle calls and wall-clock time;
- whether the final minimum changes;
- failure category when a candidate is rejected.

Run `baseline`, `SFC all`, and leave-one-family-out ablations on fresh compiler bugs. This directly tests whether SFC's extra search space buys reduction because it explores qualitatively better neighborhoods or merely because it spends more queries/time.

A second modern-toolchain axis is to repeat the same cases across pinned Perses/grammar/toolchain revisions. That can quantify **grammar/toolchain drift** separately from the algorithmic effect.

## Promotion path

- **To L1:** obtain the exact paper artifact/result tables and recompute all reported aggregate token/time/dedup metrics from raw outputs.
- **To stronger L2:** run a fresh real bug-triggering C/Rust/SMT case through baseline Perses/Vulcan and SFC variants from the paper artifact.
- **To L3:** rerun the full benchmark and 3,796-program deduplication study with paper-equivalent versions/resources.
- **To L4:** run the equal-budget transformation-ROI and leave-one-family-out experiments above.

# SFC — Boosting Program Reduction with Syntax-Guided Transformations

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. **Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations**, PACMPL/OOPSLA 2025, DOI `10.1145/3763053`.

- Author-hosted paper: `https://cs.uwaterloo.ca/~cnsun/public/publication/oopsla25/oopsla25.pdf`
- Official replication package: `sfc-reducer/sfc-reducer`
- Pinned artifact commit: `ccf633861cdda312f5f6a6fba8a68f08cfa93888` (2026-03-24)
- Current upstream implementation: `uw-pluverse/perses`
- Pinned current-Perses commit for mechanism tests: `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27)
- Current level: **scoped L1 minimization-results recomputation + scoped L2 current-Perses mechanism**. This is not L3/paper-scale reproduction.

## Core insight

Perses-style reducers historically rely mainly on subtree hoisting and quantified-node deletion. Those operations preserve syntax, but miss valid rewrites that change one grammatical form into another. The paper adds **Structure Form Conversion (SFC)** and builds three reducers on top of it:

1. Smaller Structure Replacement — choose a strictly smaller alternative grammatical form;
2. Identifier Elimination — use SFC to remove identifier uses and expose later deletion opportunities;
3. Structure Canonicalization — rewrite equal-size structures toward a canonical grammar alternative.

The paper reports that `SFC_Perses` produces outputs 36.82%, 18.71%, and 41.05% smaller than Perses on C, Rust, and SMT-LIBv2; `SFC_Vulcan` improves over Vulcan by 14.51%, 7.65%, and 7.66%. The canonicalization experiment contains 3,796 C programs / 46 unique bugs and reports 442 / 435 additional duplicate eliminations for SFC_Perses / SFC_Vulcan.

## Reproduction performed

### Scoped L1 — released minimization results

The paper explicitly points to `sfc-reducer/sfc-reducer` as its replication package. The package contains benchmark inputs, released minimization outputs/results, conversion scripts, plotting scripts, and canonicalization result directories. `recompute_l1.py` pins the artifact commit and independently reprocesses the released per-case CSV evidence with Python's standard library.

Fresh CI recomputation:

| Comparison | Paper | Recomputed | Cases | Status |
|---|---:|---:|---:|---|
| SFC_Perses vs Perses, C | 36.82% smaller | **36.822321%** | 20 | exact at 2 dp |
| SFC_Perses vs Perses, Rust | 18.71% | **18.706362%** | 20 | exact at 2 dp |
| SFC_Perses vs Perses, SMT-LIBv2 | 41.05% | **41.054543%** | 205 | exact at 2 dp |
| SFC_Vulcan vs Vulcan, C | 14.51% | **14.509205%** | 20 | exact at 2 dp |
| SFC_Vulcan vs Vulcan, Rust | 7.65% | **7.654617%** | 20 | exact at 2 dp |
| SFC_Vulcan vs Vulcan, SMT-LIBv2 | 7.66% | **7.655586%** | 205 | exact at 2 dp |

This is **L1**, not a live reducer rerun. It currently covers the six headline minimization claims, not every table/statistical test in the paper.

### Scoped L2 — current Perses mechanism

The current public Perses tree contains the `sfc/` implementation and `PaperExampleSimplificationsTest.kt`, which explicitly encodes the **12 SFC examples from §4.1** against the real C grammar, plus focused tests for all three SFC reducers.

`reproduce.sh` pins current Perses and freshly runs with Bazel test caching disabled:

- `PaperExampleSimplificationsTest` — 12 paper examples;
- `StructureFormConverterCTest` — SFC candidate generation on the C grammar;
- `SmallerStructureReplacementReducerTest`;
- `IdentifierUseEliminationReducerTest`;
- `StructureCanonicalizationReducerTest`.

This is a fresh execution of the authors' current implementation, so it is **scoped L2 mechanism evidence**. Because the tested Perses revision is post-paper, it is not treated as a faithful rerun of the paper's historical experiment.

## Run

```bash
python3 papers/2025-sfc/recompute_l1.py
bash papers/2025-sfc/reproduce.sh
```

The first command is lightweight L1. The second requires network access plus Bazel/Bazelisk and is the current-Perses scoped-L2 lane. GitHub Actions uploads both evidence sets.

## What remains unreproduced

The official artifact documents how to rebuild/rerun the minimization study, but warns that its Docker image is based on the T-Rec image and is **over 100 GB**, making a paper-scale live rerun unsuitable for normal hosted CI. It also explicitly says **Bench-cano is not included because its authors did not release it**. Although canonicalization result directories are present, this study has not yet independently recomputed the full Table/RQ evidence from them.

Therefore:

- the six minimization headline numbers are scoped **L1**;
- current source-level SFC behavior is scoped **L2 mechanism**;
- the 245-case minimization experiment has not been freshly rerun at paper scale (**L3 missing**);
- the 3,796-program canonicalization experiment cannot be freshly regenerated from this artifact alone because Bench-cano inputs are absent.

## Experiment design for L3

Pin the paper-era SFC/Perses/Vulcan revisions, compiler/solver versions, and exact Benchmark-Reduce inputs. Run single-threaded as in the paper and preserve per-case token count, property-check queries, wall time, and final reduced program. Repeat wall-time measurements for variance, then recompute per-case percentage changes and Wilcoxon tests rather than comparing only means. The >100 GB environment should run on a persistent self-hosted runner with image/cache reuse, not a fresh hosted runner.

For canonicalization, first obtain a legally redistributable Bench-cano snapshot or exact dataset revision from its source; otherwise only released-output L1 analysis is possible.

## Threats and limitations

1. **Released-output dependence.** L1 validates published arithmetic against released outputs; it does not regenerate those outputs.
2. **Post-paper artifact drift.** The pinned official artifact commit is dated 2026-03-24, after publication; provenance is pinned, but it may contain post-publication fixes.
3. **Post-paper implementation drift.** The scoped-L2 Perses revision is from 2026-08-27 and may differ from the evaluated prototype.
4. **Missing Bench-cano inputs.** The official README explicitly states they are not included.
5. **Heavy environment.** The artifact's T-Rec-based Docker dependency is >100 GB, which raises reproducibility cost and makes ephemeral CI a poor L3 environment.
6. **Runtime sensitivity.** The paper used Ubuntu 20.04, AMD 7950X, 128 GB RAM, one thread; GitHub-hosted runners differ substantially.
7. **Benchmark age.** Historical C/Rust/SMT bugs may favor grammar structures that motivated SFC; fresh compiler bugs are needed to test generalization.
8. **Search-budget confound.** SFC trades extra search for smaller outputs, so comparisons should also normalize property-query or wall-clock budget.

## Most valuable extension — budget-normalized SFC on fresh compiler bugs

Use compiler bugs filed after the paper and compare Perses against SFC_Perses under equal **property-query budgets** and equal **wall-clock budgets**. Instrument every SFC proposal with transformation class, accepted/rejected result, token delta, downstream deletion unlocked, and oracle cost. Then run leave-one-method-out ablations for Smaller Structure Replacement, Identifier Elimination, and Structure Canonicalization.

This tests whether SFC's benefit survives benchmark/toolchain drift and identifies which grammatical conversions have positive reduction ROI instead of treating the three methods as one opaque bundle.

## Upgrade path

- **L1 broader:** recompute the ablations, time/query statistics, Wilcoxon tests, and canonicalization released-result claims.
- **L2 stronger:** run one complete fresh bug-triggering program through paper-era or provenance-matched Perses and SFC_Perses with the same oracle.
- **L3:** rerun all available Benchmark-Reduce cases under paper-like resources; canonicalization additionally requires Bench-cano access.
- **L4:** post-2025 bugs + budget-normalized baselines + method-level ablation/ROI analysis.

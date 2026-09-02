# Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. PACMPL 9(OOPSLA2), 2025. DOI: 10.1145/3763053.

Current reproduction level: **L0 implementation/provenance audit + scoped L2 live-minimal**. This is not an L1 or L3 paper-scale reproduction.

## Core insight

Syntax-guided reducers such as Perses prune invalid candidates effectively, but their common transformations can still miss smaller programs because they preserve too much of the original grammar shape. The paper introduces **Structure Form Conversion (SFC)** and three consumers of it:

1. Smaller Structure Replacement (SSR): replace a subtree with a strictly smaller grammar-equivalent structure form when the property oracle still accepts it.
2. Identifier Elimination (IE): remove uses of identifiers through structure-form alternatives.
3. Structure Canonicalization (SC): normalize equal-size structures so semantically similar bug triggers converge toward the same syntactic form.

The paper integrates these reducers into Perses/Vulcan as SFCPerses/SFCVulcan.

## Published results

The paper reports that SFCPerses reduces Perses outputs by **36.82% / 18.71% / 41.05%** on C / Rust / SMT-LIBv2, at **3.65x / 16.99x / 1.42x** the reduction time. SFCVulcan further reduces Vulcan outputs by **14.51% / 7.65% / 7.66%**, at **1.56x / 2.35x / 1.42x** the time. On 3,796 C programs covering 46 unique bugs, SFCPerses and SFCVulcan canonicalize **442** and **435** additional duplicates, respectively.

## Official implementation evidence

The current public `uw-pluverse/perses` repository contains a dedicated `sfc/` module. The reproduction pins commit:

`6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2`

At that commit, the repository exposes official golden/system tests for all three paper mechanisms:

- `smaller_structure_replacement_reduction_golden_test`
- `identifier_use_elimination_reduction_golden_test`
- `canonicalization_reduction_golden_test`

and a `PaperExampleSimplificationsTest` covering paper examples.

This is stronger than a structural source audit because CI executes the official reducer implementation end-to-end against its property-test/golden fixtures. It is still only **scoped L2**, because these are small official fixtures rather than the paper's full C/Rust/SMT benchmark suites.

## Reproduce

```bash
bash papers/2025-sfc/reproduce.sh
```

Requirements: `git`, a JDK/toolchain compatible with Perses, and `bazelisk` (or `bazel`). The script clones the pinned official Perses commit, runs the four SFC tests above, and writes logs plus a compact evidence summary under `papers/2025-sfc/results/`.

## Paper vs reproduction

| Evidence | Paper | This reproduction | Status |
|---|---|---|---|
| SSR works through a property-guarded structural replacement | evaluated at benchmark scale | official SSR golden system test | scoped L2 |
| Identifier elimination is implemented and executable | evaluated at benchmark scale | official IE golden system test | scoped L2 |
| Structure canonicalization is implemented and executable | improves duplicate canonicalization | official SC golden system test | scoped L2 |
| Paper examples simplify as intended | described in algorithm/examples | official `PaperExampleSimplificationsTest` | scoped L2 |
| C/Rust/SMT aggregate size reductions | 36.82% / 18.71% / 41.05% vs Perses | not rerun | not L1/L3 |
| 3,796-case canonicalization experiment | +442 / +435 duplicate collapses | not rerun | blocked by full benchmark/runtime cost |

## Threats and limitations

- The pinned source is a current public Perses revision, not a separately archived paper artifact snapshot. Later refactors can differ from the exact evaluation version even though the paper's SFC code remains present.
- Golden fixtures validate correctness of the implementation path, not the statistical claims over the paper benchmarks.
- The canonicalization fixture deliberately checks reducer behavior rather than C compilation, so passing it should not be interpreted as semantic equivalence of arbitrary canonicalized programs.
- Bazel/JDK dependency drift can affect buildability even when reducer logic is unchanged; the pinned Git commit does not pin all external toolchains.
- The paper's effectiveness ratios should be reprocessed from released per-case raw data before calling anything L1.

## How to reach the next levels

**L1:** locate the exact paper result tables/raw CSVs and recompute all C/Rust/SMT aggregate size/time/canonicalization claims.

**L3:** pin the paper's Perses/Vulcan revisions, all benchmark inputs and historical compilers/property checkers, then rerun the complete study with repeated trials and wall-clock accounting.

## Research-worthy extension

### Transformation ROI and modern-toolchain drift

Instrument every SFC attempt with `(rule, candidate tokens, accepted?, oracle calls, wall time, final token delta)`. Compare:

- Perses baseline;
- Perses + SSR only;
- Perses + IE only;
- Perses + SC only;
- all SFC passes;
- Vulcan + the same ablations.

Run both the historical benchmark suite and a fresh post-2025 compiler-bug set. The key metric should be **accepted token reduction per extra property-check second**, not only final size. This tests whether SFC's gains survive compiler/toolchain drift and which transformation actually pays for its additional search cost.

A second useful extension is a fairness baseline: give plain Perses/Vulcan the same wall-clock or property-check budget as SFC variants. That separates gains caused by better search structure from gains caused simply by doing more work.

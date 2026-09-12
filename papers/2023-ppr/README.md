# PPR: Pairwise Program Reduction

Mengxiao Zhang, Zhenyang Xu, Yongqiang Tian, Yu Jiang, Chengnian Sun. ESEC/FSE 2023. DOI: 10.1145/3611643.3616275.

## Core idea

Classical reducers minimize one bug-triggering program. PPR instead starts from a passing seed `Ps` and a bug-triggering variant `Pv`, and jointly minimizes (1) the seed, (2) the variant, and (3) the difference between them. The minimized difference is intended to expose the mutation/change most closely related to the bug.

The paper's pipeline combines three reducers: tree-based difference reduction (`MinTdiff`), list-based difference reduction (`MinLdiff`), and commonality reduction (`MinCommonality`). The paper reports that the order matters: difference reduction should precede commonality reduction.

## Paper claims used as references

For the 20 C compiler bugs in Benchmark-PPR, the paper reports mean sizes changing from 39,956 -> 259 tokens for seeds, 52,712 -> 278 tokens for variants, and 27,880 -> 24 tokens for the difference, corresponding to 99.35%, 99.47%, and 99.91% reduction rates. PPR takes 4.55 h on average. The paper also reports that disabling `MinCommonality` leaves much larger programs and that putting commonality first produces substantially worse results.

These numbers are **reference claims only** in this directory; this run does not reproduce the full 20-case paper experiment.

## Reproduction level

**Current level: L0 official-artifact audit + official current-source scoped L2 + independent scoped L2 mechanism reproduction.**

- **L0:** official implementation and Benchmark-PPR are public in `uw-pluverse/perses`; the paper also points to Zenodo artifact `10.5281/zenodo.8267114`.
- **Official scoped L2:** the pinned current Perses PPR implementation was built and actually run in GitHub Actions on a fresh tiny C pair with a compile-and-execute oracle.
- **Independent scoped L2:** `reproduce.py` separately models difference-first pairwise reduction on the same fresh pair using GCC.
- **Not L1:** released paper-scale result files were not reprocessed here.
- **Not L3:** the 20 C bugs, historical compiler versions, and paper-scale 24 h budgets were not rerun.

## Run

```bash
cd papers/2023-ppr
./reproduce.sh
```

The oracle requires:

- seed compiles and prints `1`;
- variant compiles and prints `2`.

The deterministic mechanism result is written to `results/result.json`.

The official-current-source lane is:

```bash
./probe_official_ppr.sh
```

## Scoped L2 results

### Independent mechanism probe

The fresh case begins with three variant-only statement changes. The compact reducer preserves only the critical `a++;` mutation while deleting irrelevant changes and common code:

| metric | original | reduced |
|---|---:|---:|
| seed token proxy | 50 | 27 |
| variant token proxy | 61 | 30 |
| changed-statement proxy | 3 | 1 |
| compile/run oracle calls | - | 19 |

This demonstrates the central mechanism: minimizing the pair can simultaneously shrink both programs and isolate a property-changing difference. It is a mechanism-level L2, not a paper-scale effectiveness claim.

### Official PPR current-source probe

GitHub Actions successfully cloned and checked out Perses commit `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27), built the official `//ppr/src/org/perses/ppr:main` target with Bazel 9.1.0, and executed PPR on the tiny pair.

Observed CI result:

| metric | official current PPR |
|---|---:|
| minimized seed | 26 tokens |
| minimized variant | 29 tokens |
| final tree-diff | 3 nodes |
| PPR execution time | 0.493 s |
| cold Bazel build | 1206.7 s (~20 min) |
| reduction status | success / parsable / no errors |

The official PPR `tree-diff` node count is **not the same metric** as the independent probe's changed-statement proxy, so `3 nodes` and `1 statement` must not be compared numerically.

Both CI evidence bundles are uploaded as `ppr-reproduction` and `ppr-official-current-source` artifacts.

## Official artifact / implementation audit

Official source: `https://github.com/uw-pluverse/perses/tree/master/ppr`

Benchmark: `https://github.com/uw-pluverse/perses/tree/master/benchmark/benchmark_ppr`

Current audited Perses commit: `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27). The current build uses Bazel 9.1.0. `probe_official_ppr.sh` pins that exact commit, builds the official PPR entry point, runs it on the tiny pair, and archives the outputs. The ~20 minute cold build is materially heavier than the deterministic independent probe.

## Paper vs reproduction

| Aspect | Paper | This reproduction |
|---|---|---|
| target | 20 GCC/LLVM bug pairs + Rust/JS generality | 1 fresh C pair |
| reducer | official PPR over Perses | official current PPR + independent mechanism probe |
| property | historical compiler bugs | distinct compile+execute outputs |
| difference reduction | tree + list | official current PPR; independent statement-level proxy |
| commonality reduction | syntax-guided tree deletion | official current PPR; independent paired common-statement deletion |
| result | 27,880 -> 24 mean diff tokens on C benchmark | official: 26/29 tokens, 3 tree-diff nodes; independent: 3 -> 1 statement proxy |
| level | paper experiment | scoped L2 only |

## Threats / limitations

1. The tiny test does not model real compiler crash/hang/miscompilation or undefined-behavior screening.
2. The independent statement-level diff is only a proxy for PPR's syntax/tree and token-based representation.
3. Compiler/toolchain drift is substantial: current Perses (2026) is not the paper-era implementation environment.
4. One deterministic case cannot estimate variance, runtime scaling, or PPR-vs-DD/Perses/C-Reduce effectiveness.
5. The official-current-source run validates present-day executability, not historical benchmark reproducibility.
6. Full historical compiler reproduction may require old toolchains, large memory, and long per-case timeouts.

## Most useful next experiment (L4)

**Mutation-localization ROI under a fixed oracle budget.** On post-2023 compiler bugs generated by mutation-based fuzzers, compare:

- independent reduction of only `Pv`;
- PPR-style pairwise reduction;
- pairwise reduction without commonality reduction;
- pairwise reduction with modern tree differencing / AST matching.

Measure final variant tokens, final diff tokens, oracle calls, wall-clock time, and whether the isolated change overlaps the known bug-inducing mutation. This tests whether PPR's extra pairwise work improves actual fault-localization information, not merely final program size.

## Upgrade path

- **L1:** obtain/reprocess the released paper result tables/logs from Zenodo and recalculate Table 1/2/3 aggregates.
- **L3:** reconstruct historical GCC/LLVM versions and rerun the 20 C Benchmark-PPR cases with paper-like timeout/resources.
- **L4:** run the fixed-budget mutation-localization experiment above on newer compiler bugs.

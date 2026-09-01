# Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction

**Paper:** ASE 2025, DOI `10.1109/ASE63991.2025.00188`  
**Authors:** Zhenyang Xu, Yiran Wang, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun  
**Official artifact:** https://github.com/uw-pluverse/latra-artifact  
**Implementation:** https://github.com/uw-pluverse/perses/tree/master/latra

## Core insight

Program reducers usually trade generality for effectiveness. Latra keeps a language-agnostic reduction engine but lets users add language-specific transformations through a compact matching/rewriting DSL. The key design point is that a useful reducer customization can be expressed as templates (`from`, `to`, holes, predicates, and optional global replacements) rather than a large language-specific reducer implementation.

The paper reports that Latra reduces **33.77% more tokens for C** and **9.17% more for SMT-LIB** than Vulcan, while producing mean final sizes close to language-specific reducers: **89 vs 85 tokens** for Latra vs C-Reduce and **103 vs 109 tokens** for Latra vs ddSMT. It also reports a **32.27% SMT-LIB execution-time improvement** over Vulcan.

## Reproduction level

| Level | Status | What is actually done here |
|---|---|---|
| L0 | ✅ | Pin and audit the public artifact and current Perses/Latra source. |
| L1 | ✅ partial | Recompute headline token statistics from the authors' published CSV outputs. This is re-analysis of author-produced results, not a fresh paper-scale run. |
| L2 | ✅ scoped | Freshly build the pinned current Perses source and run Latra's C/SMT matcher-rewriter tests. This validates the live mechanism on a modern source snapshot, not the 225-case paper experiment. |
| L3 | ❌ | Full 20 C + 205 SMT-LIB benchmark rerun is not performed. |
| L4 | design only | Toolchain/template-drift study described below. |

## Artifact audit

Pinned artifact commit: `7a9e619b74c11418f5c5d9b469227153b674d8a5`.

The GitHub artifact contains the paper-result CSVs and analysis scripts, but the README's full evaluation instructions depend on `cancel/latra-artifact:latest`. The README describes C/SMT benchmark directories and prebuilt binaries/JARs inside that Docker environment, while those full assets are not present in the GitHub repository itself. Because the Docker tag is mutable and the README does not publish a paper-era image digest, this reproduction does **not** claim a version-pinned L3 rerun.

Published summary files used for L1:

- `benchmark/c-benchmark.csv` — 20 C subjects, final token sizes for Vulcan/C-Reduce/Latra.
- `benchmark/smt-tokens.csv` — 205 SMT-LIB subjects, final token sizes for Vulcan/ddSMT/Latra.
- `benchmark/smt-queries.csv` and `benchmark/smt-time.csv` — published query/time summaries used for audit output.

Current-source probe is pinned to Perses commit `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` and Bazelisk `v1.29.0`; Perses currently requests Bazel `9.1.0` via `.bazelversion`.

## Experiment design

See [EXPERIMENT.md](EXPERIMENT.md) for hypotheses and promotion criteria. The one-command entry point is:

```bash
bash papers/2025-latra/reproduce.sh
```

Run only the deterministic L1 re-analysis:

```bash
bash papers/2025-latra/reproduce.sh --l1
```

Run only the scoped live-source probe:

```bash
bash papers/2025-latra/reproduce.sh --l2
```

Generated evidence is written to `results/` and uploaded by GitHub Actions.

## Paper vs reproduction

| Claim / metric | Paper | This reproduction | Interpretation |
|---|---:|---:|---|
| C subjects | 20 | checked from official CSV | L1 structural/data check |
| SMT-LIB subjects | 205 | checked from official CSV | L1 structural/data check |
| C mean per-subject token improvement vs Vulcan | 33.77% | recomputed by `recompute.py` | L1 partial |
| SMT mean per-subject token improvement vs Vulcan | 9.17% | recomputed by `recompute.py` | L1 partial |
| C mean final tokens, Latra / C-Reduce | 89 / 85 | recomputed from official CSV | L1 partial |
| SMT mean final tokens, Latra / ddSMT | 103 / 109 | recomputed from official CSV | L1 partial |
| SMT runtime improvement vs Vulcan | 32.27% | reported in paper; raw summary retained in audit report | not used to upgrade level |
| Live template rewriting | paper implementation | current pinned C/SMT upstream tests | scoped L2 mechanism probe |
| Full 225-subject reduction campaign | yes | not rerun | no L3 claim |

`recompute.py` asserts the two headline relative-improvement figures and paper-rounded mean token counts. CI failing these assertions is treated as evidence of artifact/schema drift rather than silently accepting a mismatch.

## Threats and limitations

1. **L1 is not a fresh experiment.** The CSVs are author-produced outputs; recomputing statistics only checks published evidence and analysis semantics.
2. **Artifact provenance is incomplete for L3.** Full benchmarks/binaries are described inside a mutable Docker image, but an immutable image digest is not documented in the public GitHub artifact.
3. **Current-source drift.** The scoped L2 probe uses a 2026 Perses snapshot, not necessarily the exact ASE 2025 implementation. Passing tests shows that the transformation mechanism still works, not that paper-scale numbers are unchanged.
4. **Resource sensitivity.** The artifact warns that parallel load can trigger property-test timeouts and change reduction effectiveness; a paper-scale rerun therefore needs controlled CPU allocation and repeated trials.
5. **Aggregate metrics hide failures.** Mean token reduction can mask transformations that regress or stop firing on a subset of benchmarks.

## Best extension: template/toolchain drift matrix

A useful L4 study is to test whether Latra's small templates age better than heavyweight language-specific reducers as compilers/solvers evolve.

Create a matrix over:

- paper-era vs current Latra/Perses;
- old vs current Clang/GCC and Z3/cvc5;
- Latra vs Vulcan vs C-Reduce/ddSMT;
- per-transformation **match count, accepted rewrite count, token delta, query count, wall time, and invalid-candidate rate**.

The important outcome is not just final size. Measuring rule firing/acceptance exposes which reduction knowledge survives toolchain drift and which templates become stale. A second ablation can disable each template family to estimate marginal value per line of customization.

## What is required for L3

1. Resolve and record the immutable digest corresponding to the paper artifact Docker image (or obtain an archival image/binary bundle from the authors).
2. Run all 20 C and 205 SMT-LIB subjects with paper-compatible versions and controlled CPU limits.
3. Repeat sufficiently to quantify timing/query variance and timeout-induced instability.
4. Regenerate Table 2 / Figure 4 from fresh outputs and compare distributions, not only means.

# WDD — Weighted Delta Debugging

Paper: **WDD: Weighted Delta Debugging**  
Authors: Xintong Zhou, Zhenyang Xu, Mengxiao Zhang, Yongqiang Tian, Chengnian Sun  
Venue: ICSE 2025  
Paper: https://arxiv.org/abs/2411.19410  
Official artifact: https://doi.org/10.5281/zenodo.14301983  
Artifact image: `wddartifact/wdd:latest`

## TL;DR

Classical ddmin partitions a list by **number of elements**. WDD observes that tree nodes can represent radically different amounts of source text, so element count is a poor proxy for how much input a deletion attempts to remove. Wddmin instead partitions near half of the **sum of element weights**; the paper uses token count as the default weight. WProbDD similarly changes ProbDD's expected gain from expected elements removed to expected **weight** removed.

The paper's motivating LLVM example reports a single ddmin partitioning step with partitions ranging from **5 to 8,752 tokens**. That is the failure mode WDD targets.

## Reproduction level

Current level: **scoped L2 mechanism reproduction + L0 artifact/claim audit**.

This is **not L1** and not a paper-scale L3 reproduction. We do not label paper numbers as reproduced unless they are recomputed from the official raw result files.

Two execution lanes are provided:

1. `reproduce.py` — deterministic fresh implementation of the core Wddmin weighted-partition mechanism, suitable for every push/PR.
2. GitHub Actions `official-demo` — pulls the authors' published Docker image and runs one official C demo benchmark through `perses_ddmin` and `perses_wdd`, preserving the generated result directories as an Actions artifact.

The full 62-case paper experiment is intentionally not run on every CI invocation. The official README says the complete experiments take **very long**, and ProbDD/WProbDD experiments are repeated **5 times** because of nondeterminism.

## Paper claims

The evaluation has **62 benchmarks**: 32 C programs and 30 XML files, using HDD and Perses as host reducers.

| Comparison | Paper result |
|---|---:|
| HDD + Wddmin vs HDD + ddmin, final size | 9.12% smaller |
| HDD + Wddmin vs HDD + ddmin, time | 51.31% less |
| Perses + Wddmin vs Perses + ddmin, final size | 0.96% smaller |
| Perses + Wddmin vs Perses + ddmin, time | 7.47% less |
| HDD + WProbDD vs HDD + ProbDD, final size | 13.40% smaller |
| HDD + WProbDD vs HDD + ProbDD, time | 11.98% less |
| Perses + WProbDD vs Perses + ProbDD, final size | 2.20% smaller |
| Perses + WProbDD vs Perses + ProbDD, time | 9.72% less |

These are paper claims, not our L1 results.

## Scoped L2 — fresh mechanism experiment

Run:

```bash
bash papers/2025-wdd/reproduce.sh
```

The synthetic input contains 19 tree-like elements with highly skewed weights and three property-essential elements. The property checker is deterministic: the failure remains iff all three essential elements remain.

Expected fresh result:

| Reducer | Property tests | Final elements |
|---|---:|---|
| count-partition baseline | 79 | `[6, 8, 10]` |
| Wddmin / real weights | 31 | `[6, 8, 10]` |
| Wddmin / uniform-weight ablation | 56 | `[6, 8, 10]` |
| Wddmin / inverted-weight ablation | 64 | `[6, 8, 10]` |

On this intentionally weight-skewed case, Wddmin uses **60.76% fewer property tests** than the count-partition baseline while reaching the same 1-minimal result. The ablation shows that the gain is not just caused by the final 1-minimal pass: destroying the weight signal increases query count.

This validates the core mechanism under a controlled fresh workload. It does **not** establish the paper's aggregate 9.12% / 51.31% results.

Generated evidence is written to `papers/2025-wdd/results/summary.json` in CI.

## Official artifact lane

The Zenodo v2 artifact states that it contains source, benchmarks, scripts, and documentation for the paper. The archive is **320.4 MB**, MD5 `2de412c8ba298e7ff861b2e293e11d11`. Its documented environment is the Docker image `wddartifact/wdd:latest` with the project at `/tmp/WeightDD`.

The CI official-demo lane selects the first published C demo case and runs:

```text
Perses + ddmin
Perses + Wddmin
```

The raw reducer outputs are copied out of the container and uploaded. This is a **fresh artifact smoke test**, but a single demo case is still scoped L2 rather than L3.

## Paper vs reproduction

| Question | Paper | This repo |
|---|---|---|
| Weighted partitioning | token-weight-aware | fresh deterministic implementation |
| 1-minimal cleanup for Wddmin | yes | implemented |
| 62-case C/XML evaluation | yes | not rerun at full scale |
| Official implementation | released in artifact/Docker | one C demo case in CI |
| ProbDD repetitions | 5 | not run in default CI |
| Aggregate effectiveness/time numbers | reported | not claimed as reproduced |
| Weight-signal ablation | discussion motivates alternatives | fresh true/uniform/inverted-weight probe |

## Experimental design for stronger L1/L3

For L1, download the official archive and recompute Tables/Figures from `results_c`, `results_xml`, `results_csv`, and `results_rq1_csv`, checking every aggregate rather than copying printed values.

For L3, rerun all 32 C + 30 XML benchmarks using the paper's Docker image and record:

- reducer and container digest;
- final token count;
- property-test count;
- wall time and CPU time;
- tokens deleted per second;
- five seeds/repetitions for ProbDD/WProbDD;
- host CPU, memory, kernel, and Docker versions.

Timing comparisons should report variance and confidence intervals rather than treating one GitHub runner observation as paper-comparable.

## Threats and limitations

**Synthetic property model.** The local L2 property is intentionally simple and independent; real compiler failures have syntax and semantic dependencies.

**Weight proxy.** Token count is cheap and general but may poorly approximate expected removal value. A huge node can be semantically essential, while a small node can unlock large downstream deletion.

**Runner timing.** GitHub-hosted runner wall time is not comparable to the paper's machine. CI is used for functional reproduction, not performance confirmation.

**Docker mutability.** The artifact documentation uses the tag `latest`. A stronger reproduction should pin the image digest; tag drift can silently change results.

**Host reducer dominance.** The paper reports smaller gains in Perses than HDD because Perses' internal transformations can dominate the delta-debugging component. A one-case smoke test cannot estimate this interaction.

## Extensions worth doing

### 1. Dynamic expected-value weighting

Replace static token count with a learned or online weight:

```text
weight(node) = estimated removable tokens × estimated property-pass probability / estimated test cost
```

Compare static tokens, AST-subtree size, compile-time cost, historical deletion success, and the combined score. This directly tests whether WDD's abstraction is stronger than its paper-era weight assignment.

### 2. Modern LLVM reducer baseline

Apply the same weight-aware partitioning idea to LLVM IR and compare against current `llvm-reduce`. Use SSA/use-def structure to define element weight and measure invalid-candidate rate, property checks, final IR instructions/tokens, and wall time.

### 3. Toolchain drift matrix

Rerun the same compiler-bug cases under paper-era vs current GCC/Clang/Perses/LLVM. Record bugs that disappear, change diagnostic/crash signature, or alter reduction difficulty. This separates reducer quality from property/toolchain drift.

## Promotion criteria

- **L1:** recompute published aggregate results from official raw result files.
- **L3:** run all 62 benchmarks with paper-like configuration and five repetitions for stochastic lanes.
- **L4:** evaluate dynamic weighting or a current LLVM `llvm-reduce` baseline on a new post-paper benchmark set.

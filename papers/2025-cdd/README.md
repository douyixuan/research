# Toward a Better Understanding of Probabilistic Delta Debugging

Mengxiao Zhang, Zhenyang Xu, Yongqiang Tian, Xinru Cheng, Chengnian Sun — ICSE 2025.

Paper: https://arxiv.org/abs/2408.04735  
Official artifact: https://zenodo.org/records/14854239  
Current implementation: https://github.com/uw-pluverse/perses

## Core insight

ProbDD looks like a Bayesian optimizer, but the paper's analysis argues that its probabilities mainly behave as monotonically increasing counters. Its practical advantage over classic `ddmin` comes largely from avoiding two low-yield query classes: complement deletion attempts and revisiting already tried subsets. This motivates CDD (Counter-Based Delta Debugging), which removes the probability machinery while retaining roughly the same subset schedule and performance.

The paper evaluates 76 benchmarks across compiler-bug reduction, software debloating, and XML processor bugs. It reports that ProbDD uses 27.01% less time and 52.44% fewer queries than ddmin across the three suites; CDD uses 29.91% less time and 52.04% fewer queries than ddmin and is statistically comparable to ProbDD in final size, time, and queries.

## Reproduction level

**Current level: L1 partial + scoped L2.**

- **L0:** verify paper/artifact/current Perses implementation and execution interfaces.
- **L1 partial:** download the authors' Zenodo v3 artifact, verify MD5, extract the released `data.csv` plus the authors' Wilcoxon scripts, and re-run those statistical calculations. This reprocesses author-provided results; it does **not** rerun the 76 benchmark reductions.
- **Scoped L2:** use the current official Perses v2.7 implementation of `CDD` and `PROBDD` on Perses' own `delta_1` C toy benchmark with a real GCC+Clang compile/run property oracle. Query counts are measured from actual property-test invocations.
- **Not L3:** the official artifact documents roughly 50–180 hours per suite/algorithm with one process and a Docker image close to 80 GB. No paper-scale live rerun is claimed.

## One-command run

```bash
bash papers/2025-cdd/reproduce.sh
```

Outputs are written to `papers/2025-cdd/results/`.

## Experiment design

### L1 partial — released-result reprocessing

`reproduce_l1.sh` downloads Zenodo record `14854239` v3 (`cdd-artifact.zip`, MD5 `21f9b3b3ef43fb2361071de32b09a2c9`), extracts only the released statistical data/scripts, and runs:

- `wilconxon_all.py`
- `wilconxon_randomness.py`

This directly checks whether the authors' released data still produces their statistical conclusions.

### Scoped L2 — current toolchain probe

The live case is copied from `uw-pluverse/perses` v2.7: `test/org/perses/benchmark_toys/delta_1/t.c` and its compile/run oracle logic. Two reductions are run with the same pipeline and deterministic mode:

1. `--default-list-minimizer-for-kleene CDD`
2. `--default-list-minimizer-for-kleene PROBDD`

Vulcan, Latra, SFC, LPR, and T-Rec are disabled. The Perses release JAR is pinned by SHA-256. The property checker compiles with GCC and Clang, runs the candidate, and requires output containing `world`.

This is a **modern implementation probe**, not a reproduction of Table IV/V. It intentionally tests toolchain drift: whether the paper's simplified CDD mechanism remains behaviorally comparable to ProbDD in the current Perses release.

## Paper vs reproduction

| Item | Paper | This reproduction |
|---|---|---|
| Benchmark scale | 76 benchmarks | released statistical data + 1 fresh upstream toy case |
| ProbDD vs ddmin | 27.01% less time, 52.44% fewer queries | L1 statistical scripts rerun; no full live suite |
| CDD vs ddmin | 29.91% less time, 52.04% fewer queries | L1 statistical scripts rerun; no full live suite |
| CDD vs ProbDD | no significant difference in size/time/query (`p=0.42/0.29/0.70`) | L1 script output recorded; scoped L2 compares fresh query counts and reduced bytes |
| Randomness | no significant impact | authors' randomness Wilcoxon script rerun |
| 1-minimality | CDD/ProbDD trade some 1-minimality for efficiency | not tested at paper scale |

The exact fresh L2 numbers are generated in `results/summary.json` by CI and should be treated only as a single-case observation.

## Official artifact blocker and L3 path

The official README states that the Docker image occupies nearly 80 GB and gives approximate single-process times of 50–100 hours for BM-C, 120–180 hours for BM-DBT, and 10–12 hours for BM-XML depending on algorithm. That is inappropriate for GitHub-hosted CI.

A manual workflow, `.github/workflows/paper-cdd-official.yml`, is provided for a dedicated self-hosted Linux x64 runner labelled `cdd-artifact` with Docker and at least ~120 GB free disk. It runs one official BM-C benchmark at a time and uploads the resulting summary/config. Repeating all 76 cases, five trials per configuration, with the paper's versions and hardware-like resources is the path to L3.

## Threats and limitations

- L1 uses released precomputed data, so it checks analysis reproducibility rather than benchmark-execution reproducibility.
- The L2 case uses Perses v2.7 (August 2026), not the paper-era implementation/environment.
- A single tiny case cannot establish equivalence between CDD and ProbDD.
- Current compilers, JVM, parser behavior, caching, and Perses defaults can change the number of property tests.
- The toy experiment measures total property-oracle invocations through Perses, not only the internal list-minimizer calls reported in every paper experiment.
- The paper's randomization conclusions require repeated trials and statistical testing; deterministic mode in L2 intentionally removes that variance.

## Most valuable extension (L4)

**Cost-aware CDD on post-paper compiler bugs.** Keep the CDD/ProbDD search policy fixed, but replace the uniform notion of a query with measured cost: compiler wall-clock time, token count, AST weight, and historical oracle latency. Compare `ddmin`, ProbDD, CDD, WDD, and cost-aware CDD under the same oracle-call and wall-clock budgets on bugs reported after the original benchmark cutoff.

This directly tests whether CDD's key lesson generalizes: the important part may not be probability at all, but avoiding low-value queries and choosing deletion subsets using a better estimate of expected reduction **per unit cost**.

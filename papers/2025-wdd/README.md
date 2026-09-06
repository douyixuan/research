# WDD: Weighted Delta Debugging

Paper: **WDD: Weighted Delta Debugging**, Xintong Zhou, Zhenyang Xu, Mengxiao Zhang, Yongqiang Tian, Chengnian Sun, ICSE 2025. DOI: `10.1109/ICSE55347.2025.00071`. Public preprint: arXiv `2411.19410`.

Official artifact: `weightdd/WeightDD`, also archived on Zenodo (`10.5281/zenodo.14301983`). This reproduction pins the GitHub artifact to commit `4a6cdd00f3f136867f23f76057a7104961c2e8e4`.

## Core insight

Classical delta debugging partitions elements by **count**. WDD observes that reducible fragments can have very different sizes, so equally sized partitions can represent very unequal removal opportunities. `Wddmin` instead partitions toward similar **total fragment weight**; `WProbDD` likewise incorporates weight into probabilistic deletion selection.

The paper evaluates WDD inside HDD and Perses on 62 real minimization benchmarks: 32 C compiler-bug programs and 30 XML/BaseX inputs.

## Reproduction level

**Current: L1 partial (RQ2 released results) + scoped L2 mechanism validation.**

- **L0:** paper, artifact, benchmark layout, scripts, and released result CSVs audited.
- **L1 partial:** `reproduce.py` downloads the eight deterministic RQ2 CSVs for `ddmin` vs `Wddmin` and re-aggregates them. Seven of eight released README aggregate rows reproduce; one current artifact value has drifted.
- **Scoped L2:** a fresh C test case is minimized by count-based ddmin and a weight-balanced Wddmin variant. Every candidate is checked by a real `gcc` compile+execute oracle.
- **Not L3:** the paper's 62-benchmark Perses/HDD experiment is not rerun.

## One-command reproduction

```bash
./reproduce.sh
```

Requirements: Python 3, GCC, and network access to the pinned public artifact CSVs. Output is written to `results/summary.json` and `results/run.log`.

## Experiment design

### L1: released-result recomputation

The script fetches:

- HDD: `hdd_ddmin_{c,xml}.csv`, `hdd_wdd_{c,xml}.csv`
- Perses: `perses_ddmin_{c,xml}.csv`, `perses_wdd_{c,xml}.csv`

For each file it recomputes mean reduction time and remaining tokens and compares those values with the artifact README's rounded RQ2 table.

Artifact hygiene issues discovered during the run are preserved as evidence:

1. `hdd_ddmin_c.csv` contains `c_benchmarks/clang-22337` twice. Keeping the later record yields 32 unique C subjects and reproduces the README aggregate (`39107.625 s`, `517.84375` tokens -> `39108 / 518`).
2. The XML CSVs use inconsistent headers: some are headerless and at least one has `Subject,Query,Time,Token_remaining` appended at EOF. The parser normalizes both layouts.
3. `perses_wdd_xml.csv` currently averages **1276.2 s**, whereas the artifact README reports **1273 s**. Its size value still matches at **37.5 tokens**. This is recorded as artifact/result drift rather than silently corrected.

### Scoped L2: fresh compile+execute minimization

The fresh test contains 16 independent C function fragments with deliberately non-uniform lexical sizes. The fixed harness requires functions `f3`, `f4`, and `f8`; all other fragments are removable. The oracle succeeds only when:

1. `gcc -std=c11 -O0` compiles the candidate;
2. the executable exits 0; and
3. stdout is exactly `42`.

Both reducers reached the same 1-minimal result `[3, 4, 8]`. Plain ddmin required **34** oracle calls; weight-balanced Wddmin required **21**, a **38.24%** reduction in oracle calls on this fresh synthetic case. This validates the mechanism only, not the paper-scale effectiveness claim.

## Paper vs reproduction

| Claim/evidence | Paper / official artifact | This reproduction |
|---|---:|---:|
| HDD ddmin C mean time | 39,108 s | 39,107.625 s |
| HDD Wddmin C mean time | 18,022 s | 18,021.594 s |
| HDD ddmin / Wddmin C mean size | 518 / 477 | 517.844 / 477.406 |
| Perses ddmin / Wddmin C mean time | 4,582 / 4,169 s | 4,581.563 / 4,168.844 s |
| Perses ddmin / Wddmin C mean size | 281 / 278 | 281.344 / 278.406 |
| HDD ddmin / Wddmin XML mean time | 3,152 / 2,621 s | 3,152.467 / 2,620.933 s |
| Perses ddmin XML mean time | 1,295 s | 1,295.133 s |
| Perses Wddmin XML mean time | 1,273 s | **1,276.2 s (drift)** |
| Perses ddmin / Wddmin XML mean size | 37.6 / 37.5 | 37.6 / 37.5 |
| Fresh weighted-partition mechanism | not a paper benchmark | 34 -> 21 oracle calls; same 1-minimal result |

**Released-result check: 7/8 aggregate rows match the README.** These are L1 measurements because they reprocess already released outputs. The fresh 16-fragment test is scoped L2 because it reruns a new compile+execute experiment, but it is not the official Perses/HDD implementation and cannot be generalized to the paper's 62 benchmarks.

## Threats and limitations

1. **L1 is not a fresh paper execution.** It validates aggregation and released evidence, not the original reduction runs.
2. **Only deterministic RQ2 is covered.** WProbDD/ProbDD are repeated experiments and RQ1 correlation data remain outside this automated lane.
3. **Released-data hygiene affects reproduction.** Duplicate subjects, mixed header layouts, and the 1273-vs-1276.2 s drift require explicit normalization and provenance tracking.
4. **The scoped L2 reducer is a small Python implementation.** It implements weight-balanced partitioning plus a 1-minimal pass, but it is not the authors' Perses/HDD implementation.
5. **Synthetic fragment structure is simple.** Independent functions do not exercise the AST dependencies of real compiler-bug inputs.
6. **Runtime comparisons are not portable.** Host, compiler/JVM version, storage, and concurrency affect absolute time.

## Blockers and path to higher levels

### To reach broader L1

Recompute RQ1 Spearman correlations and RQ3's five-run ProbDD/WProbDD statistics from the raw artifact, explicitly documenting run aggregation and random-seed handling.

### To reach official-implementation L2

Run at least one released C benchmark with the artifact's Perses/HDD binaries inside the official Docker image `wddartifact/wdd:latest`; record image digest, exact benchmark, oracle invocations, final tokens, and wall time. The artifact's implementation layout has changed since publication, so the exact paper-era executable path/version must be pinned rather than inferred from current `main`.

### To reach L3

Run all 32 C + 30 XML benchmarks for the compared reducers, repeat probabilistic configurations five times as prescribed, and reproduce paper-scale RQ1/RQ2/RQ3 tables on a documented host.

## Research extension / L4 proposal

**Weight metric ablation under a fixed oracle-call budget.** Compare element-count ddmin, token-weight Wddmin, AST-subtree-node weight, estimated compile-cost weight, and a learned `deletion-success × removable-size` score on post-2025 compiler bugs. Report final tokens, oracle calls, wall time, variance, and `tokens removed / oracle call`.

This tests whether WDD's gain comes from token size specifically or from the more general principle of cost-aware partitioning. A fair modern baseline should include current Perses because later reducer/toolchain evolution can otherwise distort a paper-era comparison.

# WDD: Weighted Delta Debugging

Paper: **WDD: Weighted Delta Debugging**, Xintong Zhou, Zhenyang Xu, Mengxiao Zhang, Yongqiang Tian, Chengnian Sun, ICSE 2025. DOI: `10.1109/ICSE55347.2025.00071`. Public preprint: arXiv `2411.19410`.

Official artifact: `weightdd/WeightDD`, also archived on Zenodo (`10.5281/zenodo.14301983`). This reproduction pins the GitHub artifact to commit `4a6cdd00f3f136867f23f76057a7104961c2e8e4`.

## Core insight

Classical delta debugging partitions elements by **count**. WDD observes that reducible fragments have very different sizes and that heavier fragments are empirically less likely to be deletable. It therefore makes the search weight-aware. `Wddmin` partitions toward similar **total fragment weight** rather than similar element counts; `WProbDD` also incorporates weight into probabilistic deletion selection.

The paper evaluates WDD inside HDD and Perses on 62 real test-input-minimization benchmarks: 32 C compiler-bug programs and 30 XML/BaseX inputs.

## Reproduction level

**Current: L1 partial (RQ2 released results) + scoped L2 mechanism validation.**

- **L0:** paper, artifact, benchmark layout, scripts, and released result CSVs audited.
- **L1 partial:** `reproduce.py` freshly downloads the eight deterministic RQ2 CSVs for `ddmin` vs `Wddmin`, re-aggregates them, and checks the public artifact's Table-1 summary values.
- **Scoped L2:** a fresh C test case is minimized by count-based ddmin and a weight-balanced Wddmin variant. Every candidate is tested by a real `gcc` compile+execute property checker. This validates the Wddmin mechanism only.
- **Not L3:** we do not rerun the paper's 62-benchmark Perses/HDD experiment.

## One-command reproduction

```bash
./reproduce.sh
```

Requirements: Python 3, GCC, and network access to the pinned public artifact CSVs. Output is written to `results/summary.json` and `results/run.log`.

## Experiment design

### L1: released-result recomputation

The script fetches these pinned artifact files:

- HDD: `hdd_ddmin_{c,xml}.csv`, `hdd_wdd_{c,xml}.csv`
- Perses: `perses_ddmin_{c,xml}.csv`, `perses_wdd_{c,xml}.csv`

For each file it recomputes mean reduction time and remaining tokens, then checks the artifact README's rounded RQ2 table. It also pairs subjects and reports mean per-subject percentage changes across the C and XML suites.

A reproducibility anomaly is made explicit rather than silently hidden: `results_csv/hdd_ddmin_c.csv` contains `clang-22337` twice. The public README's C/HDD mean is recovered only when the later row is retained. The script therefore uses **keep-last by Subject** and reports every duplicate it encounters.

### Scoped L2: fresh compile+execute minimization

The fresh test contains 16 independent C function fragments with deliberately non-uniform lexical sizes. The fixed harness requires functions `f3`, `f4`, and `f8`; all other functions are removable. The property checker succeeds only when:

1. `gcc -std=c11 -O0` compiles the candidate;
2. the executable exits 0; and
3. stdout is exactly `42`.

Both reducers must reach the same three-fragment 1-minimal result. We then compare property-check counts. Fragment weights are measured from generated C lexical tokens, not supplied as arbitrary scores.

## Paper vs reproduction

| Claim/evidence | Paper / official artifact | This reproduction |
|---|---:|---:|
| HDD-Wddmin on C, mean time | 18,022 s vs 39,108 s | recomputed in CI |
| HDD-Wddmin on C, mean remaining size | 477 vs 518 tokens | recomputed in CI |
| Perses-Wddmin on C, mean time | 4,169 s vs 4,582 s | recomputed in CI |
| Perses-Wddmin on C, mean remaining size | 278 vs 281 tokens | recomputed in CI |
| HDD-Wddmin on XML, mean time | 2,621 s vs 3,152 s | recomputed in CI |
| Perses-Wddmin on XML, mean time | 1,273 s vs 1,295 s | recomputed in CI |
| Fresh weighted-partition mechanism | not a paper benchmark | compile+execute scoped L2 |

The final values in this table are intentionally not upgraded to L3 evidence: L1 reprocesses already released measurements, while the L2 probe is a new tiny test rather than a rerun of the paper benchmark suite.

## Threats and limitations

1. **L1 is not a fresh execution.** It validates aggregation and released evidence, not the original reduction runs.
2. **Only deterministic RQ2 is covered.** WProbDD/ProbDD are repeated experiments and RQ1 correlation data are outside today's automated lane.
3. **Artifact row duplication matters.** A naive 33-row mean for `hdd_ddmin_c.csv` does not reproduce the README; deduplication policy changes the result.
4. **The scoped L2 reducer is a small Python implementation.** It matches the paper's weight-balanced partition idea and explicit 1-minimal pass, but it is not the authors' Perses implementation.
5. **Synthetic fragment structure is simple.** Independent function definitions do not exercise AST dependency interactions seen in real compiler-bug inputs.
6. **Runtime comparisons are not portable.** The paper's time results depend on host, compiler, JVM, storage, and concurrency; L1 only recalculates the recorded times.

## Blockers and path to higher levels

### To reach broader L1

Recompute RQ1 Spearman correlations and RQ3's five-run ProbDD/WProbDD statistics from the raw released artifact, explicitly documenting run aggregation and random-seed handling.

### To reach L2 with the official implementation

Run at least one released C benchmark with the artifact's Perses/HDD binaries inside the official Docker image `wddartifact/wdd:latest`; record image digest, exact benchmark, oracle invocations, final tokens, and wall time.

### To reach L3

Run all 32 C + 30 XML benchmarks for the compared reducers, repeat probabilistic configurations five times as prescribed, and reproduce paper-scale RQ1/RQ2/RQ3 tables on a documented host.

## Research extension / L4 proposal

**Weight metric ablation under a fixed oracle-call budget.** Compare element-count ddmin, token-weight Wddmin, AST-subtree-node weight, estimated compile-cost weight, and a learned deletion-success × removable-size score on post-2025 compiler bugs. Report final tokens, oracle calls, wall time, variance, and `tokens removed / oracle call`.

This directly tests whether WDD's gain comes from the specific token-size proxy or from the more general principle of cost-aware partitioning. A fair baseline should also include current Perses, because later Perses releases have absorbed several reduction ideas and can otherwise make a paper-era comparison misleading.

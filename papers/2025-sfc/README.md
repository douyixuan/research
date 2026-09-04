# SFC — Syntax-Guided Transformations for Program Reduction

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. **Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations**, OOPSLA 2025. DOI: `10.1145/3763053`.

Official artifact: `sfc-reducer/sfc-reducer`, pinned here at `ccf633861cdda312f5f6a6fba8a68f08cfa93888` (2026-03-24).

Current level: **L1 for the released 245-case minimization results + L0 artifact/live-run audit**. This is not L2 or L3: the reducers were not freshly rerun.

## Core insight

General syntax-guided reducers such as Perses and Vulcan preserve syntactic validity but cannot perform many useful language-aware rewrites. SFC adds three transformation families around an existing reducer:

1. **SSR — Smaller Structure Replacement**: replace a construct with a smaller compatible structure;
2. **IE — Identifier Elimination**: remove/rewrite identifier relationships that block reduction;
3. **SC — Structure Canonicalization**: normalize equivalent structures so duplicate reduced programs become visible.

The design is deliberately complementary: reuse a mature reducer for search, then expose reduction opportunities that pure subtree deletion/hoisting misses.

## What is actually reproduced

`reproduce.py` downloads the authors' released CSVs from the pinned commit and follows their plotting-script conventions exactly:

- C: 20 cases;
- Rust: 20 cases;
- SMT-LIBv2: 205 cases;
- CSV field 3 is reduction time and field 4 is output size;
- C/Rust time ratios use arithmetic mean, while the released SMT plotting script uses geometric mean;
- SFC-after-Perses/Vulcan stage times are combined with the baseline where the official scripts do so.

The CI asserts all six headline output-size improvements. Time ratios are also recomputed and recorded, but are not used to inflate the reproduction level.

Run:

```bash
bash papers/2025-sfc/reproduce.sh
```

Output: `results/l1-minimization.json`.

## Paper vs reproduction

The paper's main RQ1 reports:

| Language | SFC_Perses smaller than Perses | SFC_Vulcan smaller than Vulcan | SFC_Perses time | SFC_Vulcan time |
|---|---:|---:|---:|---:|
| C | 36.82% | 14.51% | 3.65× | 1.56× |
| Rust | 18.71% | 7.65% | 16.99× | 2.35× |
| SMT-LIBv2 | 41.05% | 7.66% | 3.97× | 1.42× |

CI recomputes these from the released per-case outputs. The generated JSON is the authoritative record of exact values for this artifact snapshot.

### Paper inconsistency found

The abstract says SFC_Perses costs **1.42×** on SMT-LIBv2, while the RQ1 main text says **3.97×**. The latter is consistent with the result section's organization; **1.42× is the SFC_Vulcan SMT value**. This reproduction therefore records both and compares the artifact calculation to the main-text RQ1 value rather than silently choosing the more favorable number.

## Artifact audit / blockers

The official package is unusually complete for L1: it includes benchmark result trees, conversion scripts, plotting scripts, reducers and binaries. However:

- the README says its Docker base is **over 100 GB**, so a fresh reducer run is not appropriate for the routine hosted-CI lane;
- the artifact explicitly says **Bench-cano is not included because its authors did not release it**, so the 3,796-program canonicalization study cannot be freshly regenerated from this artifact alone;
- canonicalization *result outputs* are present, so those claims can be independently reprocessed later as additional L1 evidence;
- the README's example commands under **“Run Vulcan” use `-r perses`**, an apparent documentation typo that should be corrected before a paper-scale rerun;
- the implementation still uses the prototype name `proteus` in paths/commands, while the paper calls the method SFC. Provenance should therefore be tracked by commit/path, not only method name.

## Experiment design to reach L2/L3

### L2 — fresh minimal

Use a Linux runner with Docker, `SYS_PTRACE`, and enough disk for the >100 GB base image. Pin the built image digest and run one C or SMT bug through:

`baseline reducer -> SFC transformations -> property oracle -> final reducer output`

Preserve input, exact command, image digest, reducer logs, oracle results, output size and wall time. Promotion to L2 requires a genuinely fresh result, not re-reading the released CSV.

### L3 — paper scale

Rerun all 20 C + 20 Rust + 205 SMT cases with the same single-thread policy as the paper. Record every case, timeout and failure, repeat wall-time measurements, and compare distributions rather than only means. The canonicalization half additionally requires obtaining Bench-cano (or constructing a clearly labeled replacement dataset); without it, the complete paper experiment is not reproducible from public inputs.

## Threats and limitations

1. **Released-output dependence:** L1 checks published evidence and arithmetic, not the reducers' ability to regenerate it today.
2. **Post-publication artifact drift:** the pinned artifact commit is from 2026, later than the 2025 paper.
3. **Large environment:** >100 GB Docker ancestry makes infrastructure capacity part of reproducibility.
4. **Missing canonicalization input:** public artifact results exist, but the underlying Bench-cano dataset does not.
5. **Metric convention drift:** arithmetic vs geometric time aggregation differs by language in the released plotting scripts.
6. **Paper-text inconsistency:** the abstract/main-text SMT time ratio conflict must not be papered over.
7. **Benchmark age:** transformation effectiveness may depend on historical compiler/solver bug shapes.

## Most valuable L4 extension — transformation ROI on fresh bugs

Use compiler/solver bugs filed after SFC's benchmark construction and compare, under an equal property-oracle-call budget:

- Perses / Vulcan;
- SFC with all SSR + IE + SC transformations;
- leave-one-family-out SFC;
- Latra templates;
- DRReduce dependency reconstruction;
- an LLM/agent reducer such as PROJ, still guarded by the same deterministic oracle.

Log transformation attempts, accepted rewrites, downstream token savings, extra oracle calls and wall time. The key question is not merely “does SFC still reduce more?” but **which transformation family creates reduction opportunities that survive toolchain/benchmark drift, and at what search cost?**

## Upgrade path

- **L1 extension:** recompute the released canonicalization/duplicate-removal claims from the stored result trees.
- **L2:** one fresh official reducer case with pinned container/environment and raw logs.
- **L3:** all 245 minimization cases, plus canonicalization only if its missing input dataset becomes available or is separately sourced.
- **L4:** fresh post-cutoff bugs + transformation-family ROI/ablation + budget-normalized modern baselines.

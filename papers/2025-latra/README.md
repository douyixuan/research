# Latra — Template-Based Language-Agnostic Program Reduction

Paper: Zhenyang Xu, Yiran Wang, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. **Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction**, ASE 2025.

- Paper DOI: `10.1109/ASE63991.2025.00188`
- Official artifact: `uw-pluverse/latra-artifact`
- Pinned artifact commit: `7a9e619b74c11418f5c5d9b469227153b674d8a5` (2026-03-28)
- Current reproduction level: **L1 partial**. This is not a full reproduction and is not currently claimed as L2.

## Core insight

Language-agnostic reducers such as Vulcan are portable but miss useful language-specific rewrites; language-specific reducers such as C-Reduce and ddSMT are effective but expensive to implement. Latra inserts a small match/rewrite DSL between reduction rounds:

`AGR reduction -> user-defined template rewrite -> property check -> AGR reduction -> ...`

The key claim is that a compact set of transformation templates can recover much of the effectiveness of bespoke language-specific reducers without embedding transformations deeply in compiler/tool internals.

The paper evaluates 20 C bug-triggering programs and 205 SMT-LIB bug-triggering programs. Its public artifact exposes result CSVs and points to a Docker image containing the benchmark/tool environment.

## Reproduction performed

### L1 partial — released-result recomputation

`reproduce.py` downloads the official CSV evidence from the pinned artifact commit and recomputes the claims using only Python's standard library.

Exactly recovered from the current public snapshot:

- C benchmark count: **20**;
- SMT-LIB benchmark count: **205**;
- C average per-case Latra token gain over Vulcan: **33.7744%** vs paper **33.77%**;
- C mean tokens: Latra **88.9**, C-Reduce **84.6** -> paper-style **89 / 85**;
- SMT-LIB average per-case token gain over Vulcan: **9.1703%** vs paper **9.17%**;
- SMT-LIB token means using the artifact plotting script's convention (`round(2)` then integer truncation): **121 / 109 / 103** for Vulcan / ddSMT / Latra, exactly matching Figure 4.

### Important artifact-snapshot drift

The current public CSV snapshot does **not** reproduce the paper-era Latra query/time columns:

| SMT-LIB metric | Paper Figure 4 | Current public CSV mean | Result |
|---|---:|---:|---|
| Tokens, Vulcan / ddSMT / Latra | 121 / 109 / 103 | 121.51 / 109.09 / 103.57 | matches under paper's integer-truncation convention |
| Queries, Vulcan / ddSMT / Latra | 23,708 / 2,600 / 26,048 | 23,708.62 / 2,600.95 / **12,517.76** | Latra column differs materially |
| Time, Vulcan / ddSMT / Latra | 1,360 / 230 / 733 | 1,360.88 / 230.55 / **246.72** | Latra column differs materially |
| Latra time gain vs Vulcan | **32.27%** reported | **60.11%** mean per-case gain in current CSV | does not match |

This is why the level is **L1 partial**, not L1-complete. The repository does not rewrite the released data to fit the paper. The simplest interpretation is that the public artifact committed after publication contains a different Latra result snapshot for query/time evidence; the cause is not established.

## L2 official-artifact attempt and blocker

A real one-case L2 probe was added for the motivating SMT-LIB benchmark `btor2-bug-12208-547`, using the authors' exact `run_alternating.py` flow and `cancel/latra-artifact:latest` image.

The first live CI attempt showed that pulling the official image dominates a normal PR check and did not complete within the practical daily validation window. Therefore the heavy lane is retained as **`workflow_dispatch` only**, while L1 remains automatic on every relevant PR/push. Until the Docker experiment completes and yields fresh parsed output, this study remains **L1 partial**.

To promote to L2, the runner needs:

- Linux + Docker with `SYS_PTRACE` capability;
- enough network/disk budget to pull `cancel/latra-artifact:latest`;
- the resolved image digest recorded before execution;
- enough wall time to run one alternating Latra/Vulcan benchmark and preserve raw output.

## Run

Automatic deterministic L1:

```bash
bash papers/2025-latra/reproduce.sh
```

Manual official-artifact L2:

```text
Actions -> paper-latra -> Run workflow
```

## Paper vs reproduction

| Claim | Paper | This repo | Status |
|---|---:|---:|---|
| C benchmark count | 20 | 20 | L1 exact |
| SMT-LIB benchmark count | 205 | 205 | L1 exact |
| Latra token gain vs Vulcan, C | 33.77% | 33.7744% | L1 exact |
| Latra / C-Reduce mean C tokens | 89 / 85 | 88.9 / 84.6 | L1 exact |
| Latra token gain vs Vulcan, SMT-LIB | 9.17% | 9.1703% | L1 exact |
| Vulcan / ddSMT / Latra SMT token means | 121 / 109 / 103 | 121.51 / 109.09 / 103.57; paper-style ints 121 / 109 / 103 | L1 exact |
| Latra SMT query mean | 26,048 | 12,517.76 in current artifact | snapshot mismatch |
| Latra SMT time mean | 733 | 246.72 in current artifact | snapshot mismatch |
| Latra SMT speed gain | 32.27% | 60.11% current mean per-case gain | snapshot mismatch |
| Full 20 C + 205 SMT rerun | paper scale | not rerun | L3 missing |
| One fresh official Docker case | n/a | scaffolded; image pull is current blocker | L2 not yet achieved |

## Experiment design for L3

A faithful paper-scale rerun should pin the Docker image by digest, then execute:

1. all 20 C cases with Vulcan, Latra, and C-Reduce;
2. all 205 SMT-LIB cases with Vulcan, Latra, and ddSMT;
3. identical CPU parallelism and timeout policy for every reducer;
4. raw token/query/time outputs for every case;
5. per-case statistics rather than only aggregate means;
6. repeated runs for wall-time variance even when token outcomes are deterministic;
7. both the paper-era tables and the current artifact snapshot as separate comparison targets.

The artifact README warns that excessive parallelism can trigger timeouts and change reduction effectiveness. Runner saturation is therefore an experimental variable, not only infrastructure detail.

## Threats and limitations

1. **Post-publication artifact drift.** The 2026 public snapshot contains query/time evidence different from the 2025 paper, so provenance must be tracked per file/commit rather than by repository name alone.
2. **Released-output dependence.** L1 validates arithmetic and released evidence, not regeneration by the reducers.
3. **Mutable Docker tag.** The official instructions use `cancel/latra-artifact:latest`; any successful L2/L3 run must record and then pin its digest.
4. **Toolchain/runner drift.** Solver/compiler crashes, Java/Python environments, host kernels, CPU contention, and timeouts can alter both time and final reduction size.
5. **Mean hides regressions.** Latra is not smaller on every case; average percentage improvement can hide rules that hurt search.
6. **Engineering-cost measurement.** LOC is useful but incomplete; template authoring/debugging time and required language expertise also matter.
7. **Benchmark age/leakage.** A hand-designed transformation catalog may overfit historical reducer benchmarks.

## Most valuable extension — transformation ROI on fresh bugs

Run Latra on compiler/solver bugs filed after the original transformation rules were written and log every template application. For each rule measure attempted applications, property-preserving acceptances, downstream token savings, added oracle calls/wall time, and failure category.

Compare under the same oracle-call budget:

1. Vulcan only;
2. Latra with original rules;
3. Latra with leave-one-rule-out ablations;
4. Latra with a small automatically mined/LLM-proposed rule set, still guarded by the deterministic property oracle.

This tests whether Latra's advantage comes from the transformation framework itself or from a benchmark-specific rule portfolio, and connects directly to newer PROJ/LPR+/DRReduce work.

## Upgrade path

- **L2:** finish at least one fresh official Docker case with pinned image digest and raw reducer logs.
- **L3:** rerun all 225 paper benchmarks under pinned resources and compare distributions against both paper-era and current-public snapshots.
- **L4:** fresh post-2025 bugs plus rule-level ROI/ablation and budget-normalized baselines.

# Latra — Template-Based Language-Agnostic Program Reduction

Paper: Zhenyang Xu, Yiran Wang, Yongqiang Tian, Mengxiao Zhang, Chengnian Sun. **Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction**, ASE 2025.

- Paper DOI: `10.1109/ASE63991.2025.00188`
- Official artifact: `uw-pluverse/latra-artifact`
- Pinned artifact commit: `7a9e619b74c11418f5c5d9b469227153b674d8a5`
- Reproduction level: **L1 reported-results**, with a **scoped L2 official-artifact smoke** attempted in CI. L1 is not a full reproduction.

## Core insight

Language-agnostic reducers such as Vulcan are portable but miss language-specific semantic rewrites; language-specific reducers such as C-Reduce and ddSMT are effective but expensive to implement. Latra inserts a small match/rewrite DSL between reduction rounds:

`AGR reduction -> user-defined template rewrite -> property check -> AGR reduction -> ...`

The key claim is that a compact set of transformation templates can recover much of the effectiveness of bespoke language-specific reducers without embedding transformations deeply in compiler/tool internals.

The paper evaluates 20 C bug-triggering programs and 205 SMT-LIB bug-triggering programs. Its artifact publishes result CSVs and a Docker image containing the full benchmark/tool environment.

## What this reproduction does

### L1 — reprocess released results

`reproduce.py` downloads the official CSV evidence from the pinned artifact commit and recomputes the headline results using only Python's standard library.

Checks:

- C: 20 cases;
- SMT-LIB: 205 cases;
- C average per-case token improvement of Latra over Vulcan: **33.77%**;
- C rounded mean tokens: Latra **89**, C-Reduce **85**;
- SMT-LIB average per-case token improvement over Vulcan: **9.17%**;
- SMT-LIB rounded mean tokens: Latra **103**, ddSMT **109**;
- SMT-LIB average per-case time improvement over Vulcan: **32.27%**.

This is **L1**, because it recomputes numbers from already released experimental outputs rather than rerunning the reducers.

### Scoped L2 — one fresh official benchmark

CI also tries one real benchmark using the authors' Docker image and exact artifact runner:

`btor2-bug-12208-547`

This is the SMT-LIB bug used by the paper's motivating example. The workflow executes the artifact's `run_alternating.py` with Latra and Vulcan on that single benchmark and saves the parsed fresh output plus the resolved Docker image digest.

If this lane passes, it counts only as **scoped L2**: one fresh end-to-end artifact run is not the paper-scale experiment.

## Run

Deterministic L1:

```bash
bash papers/2025-latra/reproduce.sh
```

The official L2 smoke is intentionally performed in GitHub Actions because it requires Docker and the artifact image.

## Paper vs reproduction

| Claim | Paper / official artifact | This repo | Status |
|---|---:|---:|---|
| C benchmark count | 20 | asserted from released CSV | L1 exact |
| SMT-LIB benchmark count | 205 | asserted from released CSV | L1 exact |
| Latra token gain vs Vulcan, C | 33.77% average per case | recomputed | L1 exact |
| Latra / C-Reduce mean C tokens | 89 / 85 | recomputed from raw rows | L1 exact |
| Latra token gain vs Vulcan, SMT-LIB | 9.17% average per case | recomputed | L1 exact |
| Latra / ddSMT mean SMT-LIB tokens | 103 / 109 | recomputed from raw rows | L1 exact |
| Latra speed gain vs Vulcan, SMT-LIB | 32.27% | recomputed | L1 exact |
| Full 20 C + 205 SMT rerun | paper scale | not rerun | L3 missing |
| One real SMT benchmark rerun | n/a | official Docker smoke in CI | scoped L2 if green |

## Experiment design for L3

A faithful paper-scale rerun should pin the Docker image by digest, then execute:

1. all 20 C cases with Vulcan, Latra, and C-Reduce;
2. all 205 SMT-LIB cases with Vulcan, Latra, and ddSMT;
3. identical CPU parallelism and timeout policy for every reducer;
4. raw token/query/time outputs for every case;
5. per-case statistics rather than only aggregate means;
6. repeated runs for wall-time variance even when token outcomes are deterministic.

The artifact README warns that excessive parallelism can trigger timeouts and change reduction effectiveness. Therefore runner saturation is an experimental variable, not just an infrastructure detail.

## Threats and limitations

1. **Released-output dependence.** L1 validates arithmetic and released evidence, not that the reducers can regenerate those results today.
2. **Mutable Docker tag.** The official instructions use `cancel/latra-artifact:latest`; the L2 lane records the resolved digest, but a future run may receive a different image unless the digest is pinned after verification.
3. **Toolchain drift.** Reducer runtimes, compiler/solver crashes, Java/Python environments, and host kernels can affect timeouts and therefore final reduction size.
4. **Mean hides regressions.** Latra is not smaller on every case; average percentage improvement can obscure cases where a template hurts search or adds cost without progress.
5. **Engineering-cost measurement.** LOC is useful but incomplete. Template authoring/debugging time and required language expertise should also be measured.
6. **Benchmark age/leakage.** A transformation catalog tuned on historical reducer benchmarks may overstate generalization to newly filed compiler/solver bugs.

## Most valuable extension — transformation ROI on fresh bugs

Run Latra on compiler/solver bugs filed after the original transformation rules were written and log every template application. For each rule measure:

- attempted applications;
- property-preserving acceptances;
- downstream token savings enabled;
- extra oracle calls and wall time;
- failures by syntactic vs semantic cause.

Compare four conditions under the same oracle-call budget:

1. Vulcan only;
2. Latra with the original rules;
3. Latra with leave-one-rule-out ablations;
4. Latra with a small automatically mined/LLM-proposed rule set that is still deterministically property-checked.

This tests whether Latra's main advantage is the DSL/framework itself or a benchmark-specific hand-crafted transformation portfolio, and directly connects to modern agentic reducer work such as PROJ/LPR+.

## Upgrade path

- **L2:** one or more fresh official Docker runs with recorded image digest and raw reducer logs.
- **L3:** rerun all 225 paper benchmarks under pinned resources and compare distributions to the published CSVs.
- **L4:** fresh post-2025 bugs plus rule-level ROI/ablation and budget-normalized baselines.

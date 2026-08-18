# OATest: Optimization-Aware Test Generation for Deep Learning Compilers

ICSE 2026 — Qingchao Shen, Zan Wang, Haoyang Ma, Yongqiang Tian, Lili Huang, Zibo Xiao, Junjie Chen, Shing-Chi Cheung.

- Paper: https://doi.org/10.1145/3744916.3773216
- Preprint: https://arxiv.org/abs/2511.18918
- Official artifact: https://github.com/ShenQingchao/OATest
- Artifact pin used here: `20d7464201f35c0552777cf7de4d696cb7b1ecd1`

## Status

**Current reproduction level: L1 — released-artifact claim reprocessing.**

Today we reprocess the authors' released bug corpus and artifact structure, pin provenance, and run source syntax checks in GitHub Actions. This is **not** a fresh OATest fuzzing campaign and must not be described as L2/L3.

## Core insight

Normal random graph generators often reach a compiler but fail to exercise the optimization logic that matters. OATest starts from a much stronger source of intent: the compiler's own documented optimization tests.

The pipeline is roughly:

```text
documented optimization tests
        ↓ instrumentation
<graph pattern, optimization pass>
        ↓ granularity-aware extraction
optimization-aware patterns
        +
seed graph contexts
        ↓ synthesis
compatible-edge reuse OR bridge-node repair
        ↓
valid optimization-aware graph
        ↓
compiler + crash / inconsistency oracle
```

The key research idea is therefore not simply "generate more graphs"; it is **preserve a known optimization trigger while varying the surrounding context**. That changes the search distribution from generic model validity toward optimization-path diversity.

## Paper claims we care about

| Claim | Paper result | This reproduction |
|---|---:|---|
| Previously unknown bugs | 56 | recomputed from released bug table in CI |
| TVM / ONNXRuntime bugs | 40 / 16 | recomputed in CI |
| Confirmed or fixed | 42 | recomputed in CI |
| Fixed | 24 | recomputed in CI |
| TVM optimizations targeted | 65 | released corpus directory audit |
| ONNXRuntime optimizations targeted | 46 | released corpus directory audit |
| Extracted patterns | 942 TVM / 2,116 ORT | recorded as paper claims; file count is audited but not equated with patterns |
| Full comparative fuzzing | 12 h × 5 repetitions per setting | **not rerun** |

The published ICSE version reports 56 bugs and 42/24 confirmed/fixed. The older arXiv abstract currently shows 58/36, so the conference paper and released artifact are treated as the authoritative final claims here. This version drift is itself worth tracking in reproducibility work.

## What `reproduce.sh` actually proves

1. pins and clones the official artifact;
2. syntax-checks the released TVM/ORT Python sources without requiring historical compiler builds;
3. parses the released bug table and independently recomputes bug/status/compiler counts;
4. checks optimization-corpus structure;
5. emits machine-readable `report.json`, human-readable `report.md`, and provenance.

Run:

```bash
bash papers/2026-oatest/reproduce.sh
```

## Experimental design in the paper

The main subjects are historical TVM commit `292ecfd` and ONNXRuntime commit `5c1b7cc`. OATest extracts optimization patterns from documented tests, combines them with seed graphs, and checks crashes plus numerical inconsistencies. The paper's main comparison uses repeated fixed-budget fuzzing and evaluates bug discovery, optimization/code coverage, optimization-trigger rate, and generation efficiency.

## Threats / limits of today's reproduction

- We did not build the historical TVM or ONNXRuntime revisions.
- We did not rerun graph synthesis or fuzzing, so no fresh bug-discovery evidence is claimed.
- Released data can validate published accounting but cannot independently validate the generator's stochastic effectiveness.
- Compiler issue state alone is not reliable ground truth for whether a bug remains: TVM #17488 is still open while its fixing PR #17501 was merged in November 2024.
- The arXiv abstract and final ICSE paper have different bug-count snapshots; reproducibility must pin paper/artifact versions, not just a title.

## Most useful extensions

### 1. Pass-conditioned context selection

OATest preserves an optimization pattern but still has a large context-search space. Replace random context/injection choices with retrieval or coverage-guided selection conditioned on the target pass.

Measure **optimization-triggered new-edge yield per 1,000 valid tests** rather than only total coverage. This separates "can generate valid graphs" from "efficiently reaches new optimization behavior".

### 2. Compiler-version drift matrix

Run the same minimized optimization-triggering tests against:

```text
paper-era commit → fixing commit → current release → current main
```

Track `reproduces / fixed / regressed / no-longer-valid`, plus pass-trigger drift. This turns the artifact into a long-lived compiler-regression benchmark instead of a frozen paper snapshot.

### 3. Stronger inconsistency oracle

The numerical oracle uses a fixed tolerance. Add dtype/operation-aware tolerances and, where feasible, symbolic/metamorphic equivalence checks. Report how many findings are sensitive to oracle choice.

### 4. Bug-status provenance

Derive fix state from merged PR/commit ancestry rather than GitHub issue open/closed status. The #17488/#17501 mismatch is a concrete example.

## Next reproduction levels

- **L2:** reproduce one historical OATest-found TVM bug end-to-end, including the optimization pass and the post-fix behavior.
- **L3:** build the exact paper compiler revisions and rerun the paper-scale repeated campaigns/baselines.
- **L4:** evaluate pass-conditioned context selection or compiler-version drift with statistically repeated trials.

See [`experiment-design.md`](experiment-design.md) for the concrete plan.

# DRReduce — dependency reconstruction for program reduction

Paper: **DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction**  
Authors: Qiong Feng, Xiaotian Ma, Yongqiang Tian, Wei Song, Peng Liang  
Status: arXiv:2605.19412 v1, 2026-05-19  
Paper: https://arxiv.org/abs/2605.19412  
Public data: https://github.com/XYZboom/DRReduceData  
Pinned data commit: `c3180d6f3daa083a4138b8593246b10b99414072`

## TL;DR

Syntax-guided reducers often reject useful deletions because an intermediate program stops compiling: deleting a provider leaves unresolved users, or deleting a parameter breaks call sites. DRReduce changes the search space from:

```text
delete syntax node -> invalid intermediate -> reject
```

to:

```text
delete semantic node -> reconstruct broken users -> property check -> accept/reject
```

The key contribution is therefore not just a better deletion order; it is allowing the reducer to cross otherwise-invalid intermediate states.

## Paper claims

DRReduce has three stages:

1. construct a semantic dependency graph;
2. reduce semantic nodes and reconstruct broken dependencies with typed/default replacements or coupled deletions;
3. hand the result to Perses for final syntax-guided minimization.

The paper evaluates **28** programs: 16 C cases (10 GCC + 6 Clang) and 12 Java/type-checker cases. The 12 Java cases consist of 4 Checker Framework, 2 ECJ, 2 JDK cases from prior datasets, plus **4 newly collected JDK cases**: `JDK-8271954`, `JDK-8272562`, `JDK-8293941`, and `JDK-8331717`.

| Comparison | Paper result |
|---|---:|
| DRReduce vs Perses, mean final-size improvement | 51.9% smaller |
| DRReduce vs WDD | 14.9% smaller |
| DRReduce vs CDD | 19.8% smaller |
| efficiency vs CReduce | 3.3× higher on average |
| efficiency vs Latra | 1.2× higher on average |
| reconstruction ablation: query invocations | 80.2% lower |
| reconstruction ablation: reduction time | 58.7% lower |
| reconstruction ablation: final tokens | 55.1%+ lower |

A concrete row is `gcc-65383`: DRReduce reports **122 tokens**, versus Perses **384**, WDD **144**, and CDD **156**.

## Reproduction level

Current level: **scoped L1 + scoped L2 mechanism reproduction**.

This is deliberately **not L3**. Two blockers prevent a faithful paper-scale rerun from the public repository alone:

1. the released repository is primarily a data/results package and does not expose the full DRReduce reducer or its JetBrains PSI integration;
2. at the pinned public commit, `clang/ + gcc/ + java/` contains **24 rather than 28** paper evaluation programs: all 16 C cases but only 8 of the 12 Java cases. The four newly collected JDK cases listed above are absent from `java/`.

The paper's Data Availability section says the public repository includes all bug-triggering programs, so this 24/28 mismatch is itself a reproducibility finding.

## Scoped L1 — official-data audit

`artifact_audit.py` clones the public data package at the pinned commit and verifies the released corpus shape:

- `clang/`: 6 cases;
- `gcc/`: 10 cases;
- `java/`: 8 cases;
- released paper-corpus coverage: **24/28**;
- missing paper rows: the four newly collected JDK cases above.

It also reprocesses the paper-era `gcc-65383` logs:

- Perses = **384** tokens;
- WDD = **144** tokens;
- DRReduce = **122** tokens;
- it searches the released CDD logs for the paper's 156-token result rather than fabricating it if absent.

### Artifact lane drift

The same released repository contains multiple result lanes. For `gcc-65383`, the paper-era Perses lane (`perses_result_2018`) is **384 tokens**, while another artifact-side Perses lane is **68 tokens**. The DRReduce-side nested Perses result similarly differs: paper-era final result **122** versus another lane **114**.

These alternate lanes are not treated as a new fair comparison. They show that baseline/toolchain snapshot selection can materially change the apparent result. Reducer revision and result-lane pinning are therefore part of the scientific claim, not just build hygiene.

## Scoped L2 — live mechanism reproduction

`mini_drreduce.py` performs a fresh experiment with the GitHub runner's real GCC:

1. compile and run a property-preserving C program;
2. delete a provider function while leaving its call site intact — compilation must fail;
3. delete the provider and reconstruct the surviving integer use with the paper's C integer default, `1` — compilation must succeed;
4. verify that the executable still prints `BUG` and that the reconstructed candidate is smaller.

This validates the core dependency-reconstruction mechanism end to end, but it is **our minimal model**, not the authors' implementation.

Run both lanes with:

```bash
bash papers/2026-drreduce/reproduce.sh
```

Generated evidence is written to `papers/2026-drreduce/results/` and uploaded by GitHub Actions.

## Paper vs reproduction

| Question | Paper | This repo |
|---|---|---|
| Evaluation corpus | 28 programs | public pinned package exposes 24/28 paper cases |
| `gcc-65383` Perses | 384 tokens | reprocessed from paper-era artifact lane |
| `gcc-65383` WDD | 144 tokens | reprocessed from released log |
| `gcc-65383` DRReduce | 122 tokens | reprocessed from released log |
| Full 28-case mean improvements | 51.9% / 14.9% / 19.8% | not claimed: four paper cases are absent and exact lane mapping is required |
| Reconstruction crosses invalid intermediate | yes | fresh GCC mechanism test |
| Full DRReduce implementation rerun | yes in paper | blocked: reducer/PSI implementation not public in data package |
| Paper-scale timing/query counts | reported | not rerun |

## Experimental design for faithful L3

A paper-scale rerun should first recover the missing four Java cases and the actual DRReduce implementation, then pin:

- DRReduce source revision and CLion/IntelliJ PSI version;
- compiler versions used by each property script;
- Perses/WDD/CDD/CReduce/Latra revisions;
- paper-era baseline lanes (`*_2018` where applicable);
- CPU, JVM, timeouts and process limits;
- per-run final token count, property-check invocations and wall time.

Timing-sensitive experiments should be repeated and report variance instead of one wall-clock observation.

## Threats and failure modes

**Artifact completeness.** The paper evaluates 28 programs, but the pinned public `clang/gcc/java` release exposes only 24. Aggregate paper numbers cannot be honestly reconstructed from this snapshot alone.

**Artifact lane ambiguity.** A naive parser can silently select the 68-token Perses lane rather than the paper's 384-token lane for `gcc-65383`.

**Property-aware semantics.** Default substitution can destroy the exact value/type relation that triggers a compiler bug. The paper's `cf-691` example demonstrates this: WDD reaches 95 tokens while DRReduce remains at 454.

**Implementation availability.** Released outputs permit scoped L1 auditing but not a faithful rerun of semantic graph construction and reconstruction search.

**Timing comparability.** Semantic analysis has an up-front cost, while successful early reduction makes later property checks cheaper. Query count and wall time can therefore tell different stories.

## Extensions worth doing

### 1. LLVM-IR DRReduce + Alive2

LLVM IR already exposes use-def chains and SSA dependencies, making graph construction simpler than source-level PSI analysis. A strong extension is:

```text
llvm-reduce
vs
llvm-reduce + dependency-aware coupled deletion
vs
llvm-reduce + reconstruction + Alive2 filtering
```

Generate type-correct reconstruction candidates, then use Alive2 to reject candidates that introduce unacceptable semantic changes. Measure final IR size, property-check count, invalid-candidate rate, wall time and bug survival.

### 2. Property-aware reconstruction policy

Instead of one fixed default, rank candidates such as same-semantics replacement, dominating value, same type class, constant, or null/default. Evaluate especially on value/type-sensitive failures such as `cf-691`.

### 3. Baseline-version matrix

Use the released `gcc-65383` 384-vs-68 Perses discrepancy as a starting point. Build a reducer/compiler revision matrix to quantify how stable program-reduction conclusions are under toolchain drift.

## Promotion criteria

- **stronger L1:** obtain the missing four Java artifacts and reconstruct all 28 rows plus the 51.9% / 14.9% / 19.8% aggregates with explicit lane mapping;
- **L3:** obtain/build the actual DRReduce implementation and rerun all 28 properties at paper-like scale;
- **L4:** implement LLVM-IR + Alive2 reconstruction or the baseline-version matrix and compare against a pinned baseline.

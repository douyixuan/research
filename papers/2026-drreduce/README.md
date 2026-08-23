# DRReduce — dependency reconstruction for program reduction

Paper: **DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction**  
Authors: Qiong Feng, Xiaotian Ma, Yongqiang Tian, Wei Song, Peng Liang  
Status: arXiv:2605.19412 v1, 2026-05-19; manuscript submitted to a journal  
Paper: https://arxiv.org/abs/2605.19412  
Public data: https://github.com/XYZboom/DRReduceData  
Pinned data commit: `c3180d6f3daa083a4138b8593246b10b99414072`

## TL;DR

Syntax-guided reducers often reject useful deletions because the intermediate program stops compiling: remove a declaration and surviving uses become unresolved; remove a parameter and call sites no longer match. DRReduce adds a lightweight semantic dependency graph and **repairs dependencies after a deletion** before asking the property checker whether the bug still reproduces.

The useful research idea is not "more clever deletion order". It is to change the search space from:

```text
delete syntax node -> invalid program -> reject
```

to:

```text
delete semantic node -> reconstruct broken users -> property check -> accept/reject
```

This lets the reducer cross intermediate states that syntax-only search cannot traverse.

## Paper claims

DRReduce has three stages:

1. build a semantic dependency graph from source analysis (or directly from an IR with explicit dependencies);
2. use DDMin over semantic nodes and reconstruct broken dependencies with typed/default replacements or coupled deletions;
3. hand the semantically reduced program to Perses for final syntax-guided minimization.

The paper evaluates 28 real bug-triggering programs: 16 C cases (Clang + GCC) and 12 Java/type-checker cases. Reported results:

| Comparison | Paper result |
|---|---:|
| DRReduce vs Perses, mean final-size improvement | 51.9% smaller |
| DRReduce vs WDD | 14.9% smaller |
| DRReduce vs CDD | 19.8% smaller |
| efficiency vs CReduce | 3.3× higher on average |
| efficiency vs Latra | 1.2× higher on average |
| reconstruction ablation: query invocations | 80.2% lower |
| reconstruction ablation: reduction time | 58.7% lower |
| reconstruction ablation: final tokens | 55.1% lower |

A useful concrete paper row is `gcc-65383`: DRReduce reports **122 tokens**, versus Perses **384**, WDD **144**, and CDD **156**.

## What is reproduced here

Current level: **scoped L1 + scoped L2 mechanism reproduction**.

This is deliberately **not L3**. The public repository is a data/results package; it does not expose the full DRReduce reducer implementation or the CLion/PSI integration used for C semantic analysis. Therefore the paper-scale search cannot be faithfully rerun from public code alone.

### Scoped L1 — official-data reprocessing

`artifact_audit.py` clones the public data package at the pinned commit and checks:

- the artifact contains exactly 28 evaluation-program directories across `clang/`, `gcc/`, and `java/`;
- the paper-era `gcc-65383` result is recoverable directly from the released result logs;
- Perses = 384 tokens, WDD = 144, DRReduce = 122;
- a CDD 156-token result is searched from the released CDD logs;
- alternate, non-paper-era lanes are recorded separately rather than silently mixed into the comparison.

The last point matters. The same artifact contains `gcc-65383/perses_result/` with a **68-token** result, while the paper comparison uses `perses_result_2018/` with **384 tokens**. Likewise the DRReduce-side alternate Perses lane reaches 114 tokens while the paper-era lane is 122. These are not a new fair benchmark result; they are evidence that **baseline/toolchain snapshot selection materially changes the apparent comparison**.

That makes environment pinning part of the scientific claim, not just build hygiene.

### Scoped L2 — live mechanism reproduction

`mini_drreduce.py` runs a fresh C experiment with the runner's real GCC:

1. compile and run a bug-property program;
2. delete a provider function while leaving its call site untouched — compilation must fail;
3. delete the provider and reconstruct the surviving use with a type-correct default value — compilation must succeed;
4. verify that the property checker still observes `BUG` and that the reconstructed program is smaller.

This validates the paper's central mechanism end-to-end, but it is **our minimal model**, not the authors' reducer.

Run everything with:

```bash
bash papers/2026-drreduce/reproduce.sh
```

Outputs are written to `papers/2026-drreduce/results/` and uploaded by GitHub Actions.

## Paper vs reproduction

| Question | Paper | This repo |
|---|---|---|
| Evaluation corpus exists | 28 real bug-triggering programs | Recounted from pinned public data |
| `gcc-65383` Perses | 384 tokens | Reprocessed from paper-era artifact lane |
| `gcc-65383` WDD | 144 tokens | Reprocessed from released log |
| `gcc-65383` DRReduce | 122 tokens | Reprocessed from released log |
| Full 28-case mean improvements | 51.9% / 14.9% / 19.8% | Not yet claimed; would require exact lane mapping for every baseline |
| Dependency reconstruction avoids invalid intermediate | yes | Fresh GCC mechanism test |
| Full DRReduce implementation rerun | yes in paper | **blocked: implementation not public in data package** |
| Paper-scale timings / query counts | reported | not rerun |

## Experimental design for a faithful L3

A faithful paper-scale reproduction should pin all of the following, not only the dataset:

- exact DRReduce source revision and CLion/IntelliJ PSI version;
- compiler versions used by each bug's property script;
- Perses/WDD/CDD/CReduce/Latra revisions;
- the paper-era baseline lane (`*_2018` where applicable);
- CPU model/core count, JVM version, timeouts and process limits;
- per-run raw query count, wall-clock time and final token count.

Then run all 28 cases with repeated trials for time-sensitive metrics. Final token counts should be deterministic or nearly deterministic; time and query-cost distributions should be reported with variance rather than only a single mean.

## Threats and failure modes

**Artifact lane ambiguity.** The public data repository contains multiple result variants. A naive script can select a newer/different Perses run and reverse the apparent conclusion for an individual bug.

**Property-aware semantics.** Replacing a deleted value with `0`, `null`, or another default can destroy the very value/type relation that triggers a compiler bug. The paper's `cf-691` case is the clearest warning: WDD reaches 95 tokens while DRReduce remains at 454.

**Implementation availability.** Released results are enough for L1 audits, but not for a faithful L3 rerun of semantic graph construction and reconstruction search.

**Timing comparability.** Semantic analysis has an up-front cost; per-query compilation cost falls as programs shrink. Comparing only query counts or only wall time can tell different stories.

## Extensions worth doing

### 1. LLVM-IR DRReduce + Alive2

This is the strongest follow-up for a compiler-focused project. LLVM IR already exposes use-def chains and explicit SSA dependencies, so Stage 1 becomes much simpler than CLion/PSI source analysis. Instead of blindly replacing deleted values with constants/`undef`/`poison`, generate a small set of type-correct reconstruction candidates and use Alive2 to reject rewrites that alter defined behavior beyond the required bug property.

Experiment:

```text
llvm-reduce baseline
vs
llvm-reduce + dependency-aware coupled deletion
vs
llvm-reduce + reconstruction + Alive2 filtering
```

Measure final IR instructions/tokens, property-check invocations, invalid-candidate rate, time, and bug-survival rate.

### 2. Property-aware reconstruction policy

Replace the fixed default-value strategy with a candidate ranking policy: same value, same type class, dominating value, constant, null/default. Compare final size and acceptance rate, especially on value/type-sensitive bugs such as `cf-691`.

### 3. Baseline-version matrix

The released `gcc-65383` data already shows that choosing a different Perses lane changes 384 tokens to 68. Build a matrix over reducer/compiler revisions to answer a question the paper does not: **how stable are program-reduction conclusions under toolchain drift?**

This should become a standard reproducibility check for reducer papers.

## Promotion criteria

- **to stronger L1:** reconstruct all 28 paper rows and the reported 51.9% / 14.9% / 19.8% aggregate numbers from the released data with explicit lane mapping;
- **to L3:** obtain/build the actual DRReduce implementation and rerun all 28 properties at paper-like scale;
- **to L4:** implement the LLVM-IR + Alive2 extension or the baseline-version matrix and compare against `llvm-reduce`/Perses-style baselines.

# PROJ — Semantic-aware and Self-improving Program Reduction via Agentic LLMs

Paper: Xintong Zhou, Hongxu Xu, Chunhao Liao, Puzhuo Liu, Yongqiang Tian, Chengnian Sun. arXiv:2607.03766v1, 4 Jul 2026.

- Paper: https://arxiv.org/abs/2607.03766
- Current status: **L0 structural + deterministic claim audit**. This is **not** a full PROJ reproduction.
- Public artifact status (checked 2026-08-16): the arXiv v1 paper does not provide a PROJ repository/artifact link, and a targeted GitHub repository search did not locate an official implementation. Therefore L2/L3 is blocked on implementation/benchmark release or an independent reimplementation with an LLM backend.

## Core insight

PROJ treats program reduction as a feedback-controlled reasoning task rather than a fixed transformation pipeline. A reducer agent proposes case-specific edits; a deterministic harness runs the bug/property checker before accepting them. After a reduction, a reflector agent distills successful edits into executable, language-specific strategies that are replayed deterministically on future programs.

The important architectural split is therefore:

`LLM proposes -> executable property checker decides -> accepted experience -> reflector -> executable learned reducer`

This is stronger than prompt-only memory because learned experience becomes testable code guarded by the original property oracle.

## Paper experiment design

The paper evaluates 90 bug-triggering programs: 60 C, 20 Rust, and 10 JavaScript. The C set is split into 30 training and 30 held-out cases. The default model is DeepSeek-V4-Flash. PROJ uses up to three sessions with attempt budgets 60/50/40 and compares against Perses, Vulcan, LPR, and C-Reduce. The RQ1 sequence is shuffled and repeated three times so later cases can benefit from strategies learned from earlier cases.

Primary metrics:

- effectiveness: final lexical token count;
- efficiency: reduction time;
- LLM cost: API dollars;
- RQ2: contribution/generalization of the learned reducer;
- RQ3: loop-structure, exploration-mode, model, and agent-harness ablations.

## Paper vs. our evidence

| Claim | Paper | This repo | Status |
|---|---|---|---|
| PROJ beats best baseline on final size | 39.0% C, 36.0% Rust, 38.9% JS | `check_reported_claims.py` recomputes ratio-of-suite-means: 39.1%, 36.0%, 38.7% | consistent; not raw-run reproduction |
| learned reducer is executable and property-guarded | strategies are executable passes checked by the property oracle | `mini_proj.py` independently implements the invariant on a toy C case | architecture smoke only |
| learned reducer generalizes | held-out C: learned reducer alone reaches ~159 tokens; full PROJ ~89 | not rerun | blocked |
| agentic PROJ beats C-Reduce / LPR | 90-benchmark study | not rerun | blocked |
| model robustness | DeepSeek-V4-Flash / MiMo-V2.5 / MiniMax-M3 similar | not rerun | blocked |

The slight C/JS arithmetic differences above are expected: the compact audit only has the Table-II suite means, while the table's percentage column is averaged per case. This audit checks consistency, not exact raw-data reconstruction.

## Deterministic run

```bash
bash papers/2026-proj/reproduce.sh
```

It performs two CI-safe checks:

1. audits the headline effectiveness claim against the published Table-II suite means;
2. compiles and executes a toy C program after every candidate rewrite, showing the paper's central safety invariant: a rewrite becomes durable only after the executable property checker accepts it.

Expected independent smoke result currently reduces the toy program from 66 lexical tokens to 34 while preserving output `7`.

## What is missing for L2

A faithful minimal live run needs:

1. official PROJ code or an independent reducer-agent harness;
2. at least one original bug-triggering benchmark plus its exact property checker/toolchain;
3. Perses pre-reduction;
4. an LLM compatible with the paper's tool-call loop;
5. reflector-generated executable strategies and their verification fixtures.

The paper used DeepSeek-V4-Flash and an Ubuntu 22.04 server with Intel Xeon 6348 CPUs. Exact paper-scale L3 additionally requires all 90 benchmarks, compiler versions, baseline configurations, random orderings, three repeated runs, and model/API-version pinning.

## Most useful reproduction plan

### L2 — one real compiler bug

Pick one C/Clang benchmark whose historical compiler can be containerized. Run:

`Perses -> learned reducer(empty) -> reducer agent -> property checker -> reflector -> learned reducer`

Acceptance criteria:

- every accepted edit still triggers the bug;
- final size is smaller than Perses alone;
- complete accepted/rejected trajectory is recorded;
- replaying the learned strategy is deterministic;
- a second unrelated fixture tests that the strategy is not case-overfit.

### L3 — paper-scale

Recreate the 30/30 C split plus Rust/JS suites, pin compiler/container hashes, randomize benchmark order, repeat >=3 times, and compare token count/time/cost to Perses, Vulcan, LPR, and C-Reduce.

## Threats / questions worth testing

1. **Benchmark leakage.** Many cases come from prior public reducer work. Modern LLMs may have seen both bugs and reduced forms. Re-run on post-training, newly filed compiler bugs.
2. **Model drift.** API names are not enough for reproducibility. Record provider model revision, date, prompt/tool schema, temperature, token counts, and raw responses.
3. **Order sensitivity.** RQ1 intentionally lets earlier cases teach later cases. Report distributions across many orderings and isolate how much benefit comes from lucky curriculum order.
4. **Mean-of-ratios vs ratio-of-means.** Publish raw per-case data and bootstrap confidence intervals; aggregate percentages can obscure hard regressions such as cases where PROJ is worse than C-Reduce.
5. **Executable-skill safety.** The reflector writes executable Python reduction passes. Run learned skills in a sandbox, restrict filesystem/network access, and fuzz the generated transforms themselves.
6. **Oracle cost.** Token size is only one objective. Compiler bug oracles can dominate runtime; measure number of property-check invocations separately from wall time.
7. **Strategy interference.** A growing learned reducer can create ordering conflicts. Test strategy ordering, fixpoint stability, and whether older skills degrade newer workloads.

## Extension experiments

### A. Fresh-bug evaluation

Use compiler bugs filed after the model's training cutoff. This is the cleanest test of semantic reasoning versus memorization/leakage.

### B. Harness > model hypothesis

The paper suggests the specialized harness matters more than model choice. Hold one current model fixed and compare:

- free-form coding agent;
- PROJ-style property-checked loop;
- PROJ-style loop + learned reducer.

Measure final tokens, oracle calls, dollars, accepted-edit rate, and invalid-candidate rate.

### C. Distillation quality

For every learned strategy, evaluate precision (property-preserving applications / attempted applications), coverage on held-out programs, token savings, and amortized LLM cost. Delete strategies whose maintenance cost exceeds benefit.

### D. Compiler-aware learned reducer

For LLVM/GCC bugs, augment the reflector with AST/IR facts instead of pure text rewriting. A promising direction is to synthesize transformations over Clang AST or LLVM IR and validate them with compilation plus Alive2 where applicable.

## Current conclusion

The paper's strongest idea is not simply "LLM reduces code"; it is the conversion of nondeterministic successful reasoning into deterministic, executable, property-guarded reduction knowledge. The main reproduction risk is currently artifact availability, so this directory deliberately stops at L0 plus claim/architecture checks rather than overstating the result.

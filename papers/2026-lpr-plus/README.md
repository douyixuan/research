# LPR+: Diverse Transformations for LLM-Aided Program Reduction

**Venue:** SPLASH/ISSTA 2026 Tool Demonstrations  
**Authors:** Zehua Zhang, Jiatong Liu, Xue Yao, Yongqiang Tian  
**Official tool:** https://github.com/t3-research/lpr-plus  
**Pinned source:** `fc83e86f3642e100b9521fe710108facf83e64f7`  
**Current reproduction level:** **L0 + scoped L2 live-minimal**

## Core idea

LPR showed that an LLM can add language-specific transformations after a generic reducer has made a failure-inducing program small enough for the model. LPR+ makes that transformation space explicit: it keeps LPR's five broad transformations and adds thirty refined rules mined from C-Reduce, Perses, Vulcan, and prior LPR outputs. Every proposed candidate is still untrusted: it is accepted only when it is smaller and the external interestingness oracle still passes.

The important design choice is therefore not "let the LLM rewrite the bug"; it is **LLM proposal + deterministic size check + external oracle validation**.

## Reported result

The public tool-demo abstract reports that, on the LPR C/Rust/JavaScript benchmark with `gpt-5.4-mini`, LPR+ reduces mean final size from **189.7 to 180.9 tokens** on cases completed by both protocols. That is an 8.8-token / ~4.64% reduction in mean final size, with additional model queries.

## What this reproduction actually does

### L0 — source/artifact audit

The official `t3-research/lpr-plus` repository is pinned to commit `fc83e86...`. The source package explicitly ships:

- the five original broad transformation prompts (`base5`);
- thirty refined transformations (`refined30`);
- the combined 35-rule suite (`all35`);
- a mock OpenAI-compatible provider path;
- a tiny C program and interestingness oracle;
- offline unit/smoke tests.

The repository does **not** vendor the original LPR artifact, Perses, Vulcan, C-Reduce, benchmark outputs, or API keys. Therefore the published 189.7 → 180.9 benchmark result cannot currently be independently recomputed from this source package alone. We do not label this L1.

### Scoped L2 — fresh end-to-end oracle-validated reduction

`reproduce.sh` clones the pinned official source and then:

1. runs the upstream offline unit/smoke suite;
2. asserts the transformation catalog is exactly `5 + 30 = 35`;
3. runs the official tiny C example using the mock provider and the full `all35` suite;
4. verifies the final program is smaller than the input;
5. verifies both initial and final interestingness oracles pass;
6. verifies at least one candidate is accepted and all 35 transformation prompts are attempted;
7. writes a machine-readable `results/summary.json` plus the upstream report.

This is a genuine fresh execution of the LPR+ control loop, but it does **not** reproduce the paper-scale LLM benchmark.

## Experiment design

| Question | Paper/tool-demo | This reproduction |
|---|---|---|
| Does a richer prompt catalog improve final reduction size? | Yes; 189.7 → 180.9 mean tokens | Not tested; mock provider is deterministic and non-semantic |
| Are candidates accepted only when smaller? | Required by design | Checked in live run |
| Must the bug/oracle property survive? | Required by design | Checked before and after reduction |
| Does the source expose 5 + 30 transformations? | 5 broad + 30 refined | Recounted from pinned source |
| Is the full benchmark reproducible without secrets/external artifacts? | Uses LPR benchmark + `gpt-5.4-mini` | No; benchmark outputs/API access are not bundled |

## Threats and limitations

- **Model drift:** the public result uses `gpt-5.4-mini`; future provider/model revisions can alter both size and query count.
- **Benchmark leakage:** the 50-case LPR benchmark predates the tool demo and may overlap model training data. A post-training bug set is needed for a stronger claim.
- **Cost/statistical variance:** one mean hides per-case wins/losses, query count, retry behavior, token spend, and run-to-run variance.
- **Baseline fairness:** LPR+ spends more model queries. Reduction quality should be compared under equal wall-clock, dollar, and query budgets, not only final size.
- **Artifact gap:** the source repo exposes the tool and offline tests, but not the raw benchmark result table needed for L1 recomputation.
- **Mock-provider scope:** the scoped L2 test verifies orchestration/oracle discipline, not LLM reasoning quality.

## Best next experiment: budget-normalized transformation selection

The strongest extension is to test whether all 35 prompts are worth their cost.

Compare four policies on the same fresh compiler-bug corpus:

1. `base5`;
2. `all35` in fixed order;
3. random 35-rule ordering;
4. adaptive rule selection using observed `accepted reduction tokens / provider cost` per rule and language.

Measure:

- final tokens and bytes;
- oracle calls;
- LLM queries and total provider tokens;
- wall-clock time and dollar cost;
- accepted-rule rate by transformation family;
- variance across at least 5 seeds/runs;
- failures by category: no-op, invalid syntax, oracle failure, non-smaller candidate, API failure.

The key metric should be **reduction gain per unit cost**, not final size alone.

## Compiler-focused extension

Run LPR+ on **compiler bugs published after the model's training cutoff**, with separate C/LLVM, Rust/rustc, and JavaScript engine cohorts. This directly tests benchmark leakage and generalization. For LLVM, add `llvm-reduce`/C-Reduce/Perses as non-LLM baselines and classify accepted LPR+ rules by whether they expose new follow-up opportunities for the deterministic reducer.

## Moving to the next reproduction level

To reach **L1**, obtain the exact per-case LPR/LPR+ result table used for the tool demo and recompute the reported means and paired-case subset.

To reach **L3**, additionally pin:

- the exact 50 benchmark inputs and interestingness oracles;
- original LPR/Perses/Vulcan/C-Reduce versions;
- the exact `gpt-5.4-mini` model snapshot/API semantics if available;
- prompt order, retry policy, temperature, token limits, and run seeds;
- repeated runs sufficient to estimate variance.

## Run

```bash
bash papers/2026-lpr-plus/reproduce.sh
cat papers/2026-lpr-plus/results/summary.json
```

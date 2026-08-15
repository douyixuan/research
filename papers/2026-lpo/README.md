# LPO — ASPLOS 2026

Paper: **LPO: Discovering Missed Peephole Optimizations with Large Language Models**  
Authors: Zhenyang Xu, Hongxu Xu, Yongqiang Tian, Xintong Zhou, Chengnian Sun  
Official artifact: `uw-pluverse/lpo-artifact`

## What the paper tests

LPO feeds LLVM IR functions to an LLM, asks for a more optimized version, then uses Alive2 to verify semantic refinement/equivalence. A rewrite that is verified and strictly better than LLVM `-O3` is evidence of a missed peephole optimization.

Core research question for this reproduction:

> Can the published benchmark/results be reproduced deterministically, and can a small live LLM + Alive2 run rediscover a known missed optimization under current tool/model versions?

## Reproduction matrix

| Layer | Goal | CI status | Notes |
|---|---|---|---|
| L1 reported-results | Re-run official `parse_rq1_results.py` over artifact outputs | automatic | No API key or LLVM build required |
| L2 live-minimal | Extract a tiny LLVM IR corpus, query an LLM, verify with Alive2 | planned/manual gate | Requires toolchain build and model access |
| L3 live-full | Re-run the full RQ1 model experiment | not yet | Cost/time/model-version sensitive |
| L4 extension | Compare current reasoning models and failure modes | proposed | See below |

## Experiment design

### Experiment A — deterministic RQ1 reproduction

1. Clone the official artifact at a recorded commit.
2. Run `python parse_rq1_results.py`.
3. Save stdout as the CI artifact.
4. Compare the summary with the paper-reported RQ1 numbers.

This validates that the published raw outputs support the reported aggregate result. It does **not** prove that a fresh LLM run reproduces those outputs.

### Experiment B — minimal live reproduction

Target: 3–5 previously reported LLVM missed optimizations.

Pipeline:

```text
known LLVM IR case
  -> LPO prompt/model
  -> candidate optimized IR
  -> Alive2 validation
  -> profitability check
  -> hit / miss / invalid classification
```

Record for every trial:

- model name and exact API/version when available;
- prompt and temperature/sampling configuration;
- input IR hash;
- generated IR;
- Alive2 verdict;
- instruction-count/cost delta;
- number of attempts before success;
- token/time cost.

Acceptance criterion: at least one known missed optimization is rediscovered end-to-end with a fresh model invocation and passes Alive2.

## Paper vs reproduction

| Claim/evidence | Paper | Our reproduction |
|---|---|---|
| Published RQ1 raw outputs aggregate correctly | reported | tested by CI |
| LLM can freshly rediscover known missed optimizations | reported | pending L2 |
| Alive2 filters incorrect candidates | system design | pending L2 failure analysis |
| Improvement over search-based baselines | reported against Souper/Minotaur | L1 can inspect provided baseline results; fair live rerun pending |

## Important threats to validity

1. **Model drift** — hosted LLM names do not guarantee identical weights/serving behavior months later.
2. **LLVM drift** — a previously missed optimization may already be fixed in current LLVM, changing the benchmark itself.
3. **Alive2/toolchain drift** — verifier behavior and supported IR evolve.
4. **Sampling variance** — success rate needs repeated trials, not one lucky generation.
5. **Cost bias** — comparing models only by hit count ignores token and wall-clock cost.
6. **Benchmark leakage** — public LLVM issues and artifact cases may be in model training data.

## Extensions worth testing

### E1 — frontier-model comparison

Run the same fixed cases with current reasoning and non-reasoning models. Compare:

- valid rewrite rate;
- verified profitable rewrite rate;
- unique optimizations found;
- attempts-to-first-hit;
- tokens and dollars per verified hit.

### E2 — verifier-feedback ablation

Compare:

- one-shot LLM;
- syntax-error feedback only;
- Alive2 counterexample/verdict feedback;
- full iterative loop.

This isolates how much of LPO's value comes from the model versus the verification-feedback loop.

### E3 — mutation-generated benchmark

Generate controlled LLVM IR patterns with known equivalent simplifications, then hide the target rewrite. This reduces dependence on public LLVM issue examples and provides ground truth.

### E4 — modern LLVM regression check

For every historical LPO hit, test current LLVM `main`:

- still missed;
- now optimized;
- transformed differently;
- no longer accepted IR.

This turns the artifact into a longitudinal compiler-quality benchmark.

### E5 — compiler-engineering extension

Convert verified candidates into candidate InstCombine tests / Alive2 proofs, then cluster recurring rewrite shapes. The useful output is not just a list of LLM wins but a taxonomy of optimization gaps that could guide generalized LLVM transforms.

## Next step

Move from L1 to L2 by pinning the artifact/toolchain, selecting 3–5 small benchmark cases, and adding a manually dispatched GitHub Action that performs a fresh model + Alive2 run with a repository secret for the model API key.

# Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets

- Authors: Yiwen Dong, Zhenyang Xu, Yongqiang Tian, Chengnian Sun
- Venue: ACM TOSEM, 2026
- DOI: `10.1145/3790099`
- Preprint: https://arxiv.org/abs/2503.04076
- Official artifact: https://github.com/uw-pluverse/thalia-type
- Pinned artifact commit: `08895f35945ac84e78b91db9f908f401246e3c15`
- Current reproduction level: **L1 partial**

## Core question

The paper asks whether high LLM accuracy on Java snippet type inference reflects semantic reasoning or benchmark memorization. The established StatType-SO benchmark has been public since 2017, so it could have entered model training data. The authors therefore introduce **ThaliaType**, a generator-backed benchmark intended to keep producing previously unseen snippets, and compare performance on the old and new benchmarks.

The key result is not merely that models make type-inference mistakes. It is that every evaluated LLM loses substantial accuracy on the unseen benchmark while the constraint-based SnR baseline remains comparatively stable. The paper also applies semantics-preserving transformations and finds that combined transformations damage StatType-SO performance much more consistently than ThaliaType performance, which is compatible with a memorization/leakage explanation.

## Paper claims selected for reproduction

Figure 7 reports global precision / recall / F1 for SnR, StarCoder2:15b, Llama 3.1 8B/70B, GPT-4o-mini, and GPT-4o on StatType-SO and ThaliaType.

This reproduction reprocesses the official released inference outputs using the artifact's own `process_files_precision_recall` implementation. It verifies the ten benchmark/model cells for which the current public artifact contains released result directories:

| Benchmark | Model | Paper P / R / F1 |
|---|---|---|
| StatType-SO | SnR | 95.50 / 91.46 / 93.44 |
| StatType-SO | Llama3.1-8b | 76.92 / 69.46 / 73.00 |
| StatType-SO | Llama3.1-70b | 86.08 / 83.69 / 84.87 |
| StatType-SO | GPT-4o-mini | 86.34 / 89.92 / 88.09 |
| StatType-SO | GPT-4o | 95.66 / 95.00 / 95.33 |
| ThaliaType | SnR | 84.15 / 84.43 / 84.29 |
| ThaliaType | Llama3.1-8b | 31.27 / 19.40 / 23.95 |
| ThaliaType | Llama3.1-70b | 61.58 / 25.85 / 36.41 |
| ThaliaType | GPT-4o-mini | 66.64 / 37.73 / 48.18 |
| ThaliaType | GPT-4o | 54.74 / 44.54 / 49.12 |

## What this reproduction actually does

```bash
./reproduce.sh
```

The script:

1. clones the official artifact at the pinned commit;
2. installs only the analysis dependency needed by the upstream evaluator (`scipy==1.14.0`);
3. calls the upstream `process_files_precision_recall` implementation over the released snippets and result directories;
4. recomputes global precision / recall / F1;
5. requires exact agreement to two decimals with the paper values above;
6. emits `results/thaliatype-report.json` plus a log for CI artifacts;
7. audits whether the StarCoder2 result directories needed for the remaining Figure 7 cells are present.

This is **L1 partial**, not L2/L3. No new LLM inference is performed.

## Artifact gap

The paper's Figure 7 includes StarCoder2:15b results, but the current public artifact snapshot does not expose a StarCoder2 result directory alongside the SnR/Llama/GPT outputs used by the released summarization scripts. Therefore the StarCoder2 rows are not counted as reproduced here.

The artifact is nevertheless unusually useful for future evaluation: it includes StatType-SO, ThaliaType, transformed snippets, saved model outputs, analysis scripts, and a generator path for producing new ThaliaType snippets.

## Why a fresh L2 run is deliberately gated

A faithful L2 run requires a model endpoint. The paper used GPT-4o / GPT-4o-mini via OpenAI and Llama/StarCoder through Ollama, with an A100 for the open-weight models. Running a different model without explicitly labeling it would mix reproduction with an extension.

To move to **L2**, run a small fresh ThaliaType sample with one pinned model and version, record the prompt, temperature/seed, endpoint, token usage and cost, and evaluate with the same upstream metric code. To move to **L3**, regenerate the full 300-snippet benchmark and repeat the paper-scale model matrix.

## Paper vs. reproduction

| Item | Paper | This reproduction |
|---|---|---|
| StatType-SO size | 267 snippets | uses released 267-snippet artifact |
| ThaliaType size | 300 snippets | uses released 300-snippet artifact |
| Models | SnR + 5 LLMs | SnR + 4 LLMs reprocessed |
| New inference | yes | no |
| Figure 7 metrics | 12 benchmark/model cells | 10 cells recomputed |
| StarCoder2 leakage claim | StackV2 inspection | not independently rerun |
| Semantic transformations | evaluated with all models | released outputs not yet fully re-audited here |
| Level | paper experiment | L1 partial |

## Threats and limitations

- **Artifact snapshot drift:** this reproduction pins the current decrypted-data snapshot; future upstream changes must not silently alter the evidence.
- **Model-service drift:** GPT model aliases and serving stacks evolve. A 2026 rerun must pin an exact model identifier and record the provider date.
- **Benchmark freshness is relative:** ThaliaType is designed to generate new snippets, but a fixed published ThaliaType snapshot can eventually leak into future training corpora too.
- **Popularity confounding:** the paper shows LLM recall rises sharply for common FQNs. A leakage test should control type popularity as well as benchmark age.
- **Prompt sensitivity/statistical variance:** temperature zero reduces sampling variance but does not eliminate backend/model revision variance.
- **StarCoder2 gap:** two Figure 7 cells remain unrecomputed from the released result directories.

## Most valuable extension: rolling post-cutoff benchmark

A stronger modern experiment is a **time-indexed ThaliaType protocol**:

1. generate a new benchmark after a model's documented training cutoff;
2. record benchmark-generation timestamp and artifact hash;
3. stratify FQNs by GitHub/document frequency;
4. evaluate several current models plus SnR under the same prompt and budget;
5. repeat with semantics-preserving transformations;
6. report `fresh F1`, `transformation robustness`, token cost, latency, and calibration rather than only raw F1.

This converts the paper's one-time leakage-control insight into a continuously renewable compiler/code-reasoning benchmark. A useful ablation is `old public benchmark vs fixed 2025 ThaliaType vs newly generated 2026 ThaliaType`, which separates benchmark memorization from model capability drift.

# TEMPLATEFUZZ: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs

**Paper:** Qingchao Shen, Zibo Xiao, Lili Huang, Enwei Hu, Yongqiang Tian, Junjie Chen. arXiv:2604.12232 (submitted 2026-04-14).

- Paper: https://arxiv.org/abs/2604.12232
- Paper-declared artifact: https://anonymous.4open.science/r/TemplateFuzz-2CC6
- Matching public source repository inspected here: https://github.com/FFchopon/TemplateFuzz-LLM
- Pinned matching-source commit: `c1a11268139ceaaca659bc61346bc843ab1cf874`

## Reproduction status

**L0 artifact/interface audit + scoped L2 safe mechanism reproduction.**

This is deliberately **not L1/L3**. The paper-scale experiment is a jailbreak evaluation over 12 open-source and 5 commercial models. Re-running those attacks is neither necessary for a deterministic CI smoke test nor appropriate as an unattended public workflow. The paper-declared anonymous artifact was not retrievable from the current automation environment. A public GitHub repository matches the paper's five mutation families, datasets/model-path interface, bandit/seed-pool controls, and evaluation layout, but the paper does not establish that GitHub URL as the provenance-identical artifact snapshot, so this repository does not treat it as such.

The scoped L2 lane reproduces the *mechanism* defensively: five structural chat-template mutations, first-/higher-order composition, feedback-guided roulette selection, a seed pool, and a utility-preserving admission gate. It uses only benign text and a synthetic template-integrity oracle. It does **not** send jailbreak prompts to any model.

## Core insight

TemplateFuzz treats the chat template itself as a fuzzing input rather than assuming it is fixed. It decomposes the template into five mutation surfaces:

1. **M1 — system message**
2. **M2 — user/assistant history**
3. **M3 — role markers**
4. **M4 — delimiters**
5. **M5 — generation hint**

Because composing those mutations creates a rapidly growing search space, the paper adds adaptive seed selection (Adaptive MCTS-Explore) and feedback-driven mutation-rule weighting with roulette-wheel selection. A lightweight oracle is refined through active learning to approximate a model-based judge at much lower evaluation cost.

The useful software-testing pattern is broader than jailbreak research:

`structured input decomposition -> compositional mutations -> feedback-guided search -> cheap learned/refined oracle -> utility constraint`

## Paper experiment

The paper evaluates 12 open-source LLMs (4B–70B) and 5 commercial LLMs. For the main open-model evaluation it uses AdvBench (520 prompts) for attack-success measurement and a balanced 1,140-question MMLU subset for utility/accuracy. Each fuzzing method runs 100 iterations. The implementation uses DeepSeek-Chat as a mutation candidate generator and vLLM on a server with 4 NVIDIA A800 GPUs.

Selected paper-reported results:

| Claim | Paper result |
|---|---:|
| Average Top-1 ASR over 12 open models | 90.5% |
| Average Top-5 ASR over 12 open models | 98.2% |
| Heuristic-search ablation, Top-1 | 95.58% |
| Random-search ablation, Top-1 | 74.04% |
| Genetic-search ablation, Top-1 | 83.27% |
| No-sampling-learning ablation, Top-1 | 87.88% |
| Enhanced rule judge accuracy | 88.27% |
| Model judge accuracy | 89.42% |
| Enhanced rule judge runtime for 520 outputs | <1 s |
| Model judge runtime for 520 outputs | 1,425 s |

`claim_audit.py` only checks arithmetic relationships among published numbers. It is an L0 claim audit, not a re-execution of model experiments.

## What is actually rerun here

Run:

```bash
./papers/2026-templatefuzz/reproduce.sh
```

The deterministic CI lane performs three checks:

1. **Paper-claim arithmetic audit** — preserves the paper's reported values and verifies stated deltas used in our analysis.
2. **Matching-source interface audit** — clones the public matching repository at a fixed commit, syntax-compiles its Python source, and verifies the M1–M5 / attack-mode surface without installing GPU dependencies or invoking models.
3. **Safe mechanism reproduction** — runs 60 deterministic fuzzing rounds over a benign synthetic chat template.

Expected safe-mechanism invariants:

- all five mutation families are exercised;
- first-order and higher-order mutations are composable;
- feedback changes mutation-selection statistics;
- the best candidate reaches a high synthetic parser-risk proxy while keeping synthetic benign utility >= 0.85;
- no model endpoint, model weight, API key, harmful dataset, or harmful prompt is used.

## Paper vs. reproduction

| Dimension | Paper | This reproduction |
|---|---|---|
| Mutation surface | M1–M5 | M1–M5 |
| High-order mutation | yes | yes |
| Adaptive search | Adaptive MCTS-Explore + roulette | deterministic seed-pool + feedback/rarity roulette mechanism model |
| Oracle | active-learning-refined jailbreak judge | synthetic template-integrity risk + utility oracle |
| Workload | AdvBench + MMLU | benign synthetic template only |
| Models | 12 open + 5 commercial | none |
| Scale | 100-round model experiments, multi-GPU | 60-round CPU CI smoke |
| Result reproduced | jailbreak/utility metrics | mechanism invariants only |
| Level | paper experiment | L0 + scoped L2 |

The distinction matters: a mechanism-level run cannot validate the paper's 90.5%/98.2% ASR claims.

## Blockers to higher reproduction levels

### To reach L1

Need the exact paper-declared artifact snapshot and its raw saved evaluation outputs. Then reprocess those outputs into the paper's RQ tables/figures without generating new attacks.

### To reach L2/L3 on real models

Need, at minimum:

- exact artifact provenance and dependency lock;
- AdvBench and the exact sampled MMLU subset;
- 4B–70B model weights and enough GPU memory/runtime (paper: 4×A800);
- DeepSeek candidate-generation access and the paper's exact API/model revision;
- baseline implementations/configurations for ChatBug, GPTFuzzer and TurboFuzzLLM;
- model-version/tokenizer/chat-template snapshots;
- controlled red-team environment and review of the experiment's safety boundary.

### Reproducibility risks

- **Model drift:** commercial models and open-model revisions can change behavior without paper-code changes.
- **Template/tokenizer drift:** chat-template serialization is tightly coupled to tokenizer/model versions.
- **Judge drift:** the learned/refined oracle depends on labels, rules and response distribution.
- **Benchmark leakage:** AdvBench is old and widely circulated; attack success on it may overstate performance on post-cutoff cases.
- **Stochastic variance:** mutation generation, target inference and search are stochastic; single-run ASR is insufficient.
- **Baseline fairness:** the paper substitutes DeepSeek-Chat for ChatGPT in adapted baselines; exact cost/query parity must be audited.
- **Artifact provenance:** the discoverable public GitHub source matches the paper interface, but the paper points to a separate anonymous artifact URL.

## Extensions worth doing

### 1. Defensive template-robustness matrix

Turn the attack surface into a defense regression suite. For each model/tokenizer release, apply **benign structural variants** of M1–M5 and check invariants such as role separation, system-instruction precedence, parse stability, and ordinary-task accuracy.

Report:

- invariant failures per mutation family;
- utility degradation;
- tokenizer/template version;
- regressions fixed or reintroduced across releases.

This keeps the compiler-testing-style insight—structured mutation + differential/regression oracle—without operationalizing jailbreak payloads.

### 2. Cost-normalized search ablation

Compare `uniform`, `paper-style feedback`, and a contextual-bandit selector under the same evaluation budget. Use `useful new integrity failure / 1,000 evaluations` rather than only success rate.

### 3. Oracle calibration over time

Freeze a human-labeled benign/adversarial *classification-only* response set and track judge precision/recall/FPR as model and rule versions change. This tests whether the paper's cheap-oracle advantage survives response-distribution drift.

### 4. Failure minimization

When a benign template mutation violates a security invariant, run delta debugging over template components to produce the smallest failure-inducing structural change. This connects TemplateFuzz directly to program-reduction work.

## CI output

Generated files under `results/`:

- `claim-audit.json`
- `source-audit.json`
- `safe-mechanism.json`

GitHub Actions uploads them as the `templatefuzz-reproduction-report` artifact.

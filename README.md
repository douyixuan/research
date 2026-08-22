# research

Reproducible paper-reading and experiment lab.

Primary track: papers by Yongqiang Tian, starting from 2026 and prioritizing compiler / LLVM / testing / LLM-for-compilers work.

## Contract for every paper

Each paper directory should contain:

- `README.md` — paper summary, hypotheses, experiment design, paper-vs-reproduction table, limitations, and improvement ideas.
- `reproduce.sh` — one-command reproducible entry point.
- `results/` — generated summaries/logs when appropriate.
- GitHub Actions coverage — at minimum a deterministic smoke/reproduction lane; expensive live experiments are separated and explicitly gated.

## Reproduction levels

- **L0 — structural**: artifact/source availability and commands are verified.
- **L1 — reported-results**: published artifact outputs are reprocessed to reproduce paper tables/numbers.
- **L2 — live-minimal**: a small end-to-end experiment is actually rerun.
- **L3 — live-full**: the main paper experiment is rerun at paper-like scale.
- **L4 — extension**: an ablation, new baseline, new model/workload, or other improvement is evaluated.

The repository should never call an L1 result a full reproduction.

## Papers

| Date added | Paper | Venue | Current level | CI |
|---|---|---|---|---|
| 2026-08-15 | [LPO: Discovering Missed Peephole Optimizations with Large Language Models](papers/2026-lpo/) | ASPLOS 2026 | L1 | `paper-lpo.yml` ✅ |
| 2026-08-16 | [PROJ: Semantic-aware and Self-improving Program Reduction via Agentic LLMs](papers/2026-proj/) | arXiv 2026 preprint | L0 + claim audit | `paper-proj.yml` |
| 2026-08-17 | [CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers](papers/2026-crosslangfuzzer/) | arXiv 2026 preprint | L2 scoped live bug reproduction | `paper-crosslangfuzzer.yml` ✅ |
| 2026-08-18 | [OATest: Optimization-Aware Test Generation for Deep Learning Compilers](papers/2026-oatest/) | ICSE 2026 | L1 | `paper-oatest.yml` ✅ |
| 2026-08-19 | [VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations](papers/2026-vizdetour/) | arXiv 2026 preprint | L1 + scoped L2 | `paper-vizdetour.yml` ✅ |
| 2026-08-20 | [On the Feasibility of Deduplicating Compiler Bugs with Bisection (BugLens)](papers/2026-buglens/) | ISSTA 2026 | L1 partial + scoped L2 | `paper-buglens.yml` ✅ |
| 2026-08-21 | [Bounded Exhaustive Random Program Generation for Testing Solidity Compilers (Erwin)](papers/2026-erwin/) | ICSE 2026 | scoped L2 live-minimal | `paper-erwin.yml` ✅ |
| 2026-08-22 | [Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types](papers/2026-scitix/) | ISSTA 2026 | scoped L2 mechanism model + L0 artifact probe | `paper-scitix.yml` ✅ |

## Daily workflow

One paper per day:

1. locate paper + official artifact;
2. identify claims and RQs;
3. design the smallest faithful reproduction;
4. make it runnable in GitHub Actions when feasible;
5. compare reproduced evidence with the paper;
6. identify threats to validity;
7. propose at least one meaningful extension;
8. record what would be required to move up one reproduction level.

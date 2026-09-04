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
| 2026-08-16 | [PROJ: Semantic-aware and Self-improving Program Reduction via Agentic LLMs](papers/2026-proj/) | arXiv 2026 preprint | L0 claim audit + scoped L2 control mechanism | `paper-proj.yml` + manual `paper-proj-live.yml` |
| 2026-08-17 | [CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers](papers/2026-crosslangfuzzer/) | arXiv 2026 preprint / SPLASH-ISSTA 2026 Tool Demo | L2 scoped live bug reproduction | `paper-crosslangfuzzer.yml` ✅ |
| 2026-08-18 | [OATest: Optimization-Aware Test Generation for Deep Learning Compilers](papers/2026-oatest/) | ICSE 2026 | L1 | `paper-oatest.yml` ✅ |
| 2026-08-19 | [VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations](papers/2026-vizdetour/) | arXiv 2026 preprint | L1 + scoped L2 | `paper-vizdetour.yml` ✅ |
| 2026-08-20 | [On the Feasibility of Deduplicating Compiler Bugs with Bisection (BugLens)](papers/2026-buglens/) | ISSTA 2026 | L1 partial + scoped L2 | `paper-buglens.yml` ✅ |
| 2026-08-21 | [Bounded Exhaustive Random Program Generation for Testing Solidity Compilers (Erwin)](papers/2026-erwin/) | ICSE 2026 | scoped L2 live-minimal | `paper-erwin.yml` ✅ |
| 2026-08-22 | [Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types](papers/2026-scitix/) | ISSTA 2026 | scoped L2 mechanism model + L0 artifact probe | `paper-scitix.yml` ✅ |
| 2026-08-23 | [DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction](papers/2026-drreduce/) | arXiv 2026 preprint | scoped L1 + scoped L2 mechanism | `paper-drreduce.yml` ✅ |
| 2026-08-24 | [DDMT: Delta Debugging in the Absence of Test Oracles Through Metamorphic Testing](papers/2026-ddmt/) | arXiv 2026 preprint | scoped L1 + scoped L2 mechanism | `paper-ddmt.yml` ✅ |
| 2026-08-25 | [LPR+: Diverse Transformations for LLM-Aided Program Reduction](papers/2026-lpr-plus/) | SPLASH/ISSTA 2026 Tool Demo | L0 + scoped L2 live-minimal | `paper-lpr-plus.yml` |
| 2026-08-26 | [Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets](papers/2026-thaliatype/) | ACM TOSEM 2026 | L1 partial | `paper-thaliatype.yml` ✅ |
| 2026-08-27 | [RepoTrace: Browser-Assisted Evidence Collection for GitHub Research Datasets](papers/2026-repotrace/) | SPLASH/ISSTA 2026 Tool Demo | L0 artifact audit + scoped L2 | `paper-repotrace.yml` |
| 2026-08-28 | [DebugTracker: Lightweight Process Evidence for Classroom Debugging](papers/2026-debugtracker/) | SPLASH/ISSTA 2026 Tool Demo | L0 artifact audit + scoped L2 | `paper-debugtracker.yml` ✅ |
| 2026-08-29 | [TEMPLATEFUZZ: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs](papers/2026-templatefuzz/) | arXiv 2026 preprint | L0 artifact/interface audit + scoped L2 safe mechanism | `paper-templatefuzz.yml` |
| 2026-08-30 | [Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries (DLLens)](papers/2026-dllens/) | ACM TOSEM 35(4), 2026 | L1 partial + L0 implementation audit | `paper-dllens.yml` |
| 2026-08-31 | [Rethinking LLM-aided RTL Code Optimization Via Timing Logic Metamorphosis](papers/2026-rtl-timing-metamorphosis/) | ACM TRETS 2026 (author page); public arXiv v1 2025 | L0 provenance audit + scoped L2 logic metamorphosis | `paper-rtl-timing-metamorphosis.yml` |
| 2026-09-01 | [Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction](papers/2025-latra/) | ASE 2025 | L1 partial; official L2 Docker lane scaffolded/manual | `paper-latra.yml` ✅ L1 |
| 2026-09-03 | [Update from Hell: Can Coding Agents Survive Hidden Breakage in Dependency Upgrades? (DEPBENCH)](papers/2026-depbench/) | arXiv 2026 preprint | L0 claim/artifact audit + scoped L2 public-case reconstruction | `paper-depbench.yml` ✅ |
| 2026-09-04 | [Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations (SFC)](papers/2025-sfc/) | OOPSLA 2025 | L1 released minimization results + L0 artifact/live-run audit | `paper-sfc.yml` |

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

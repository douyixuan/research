# Yongqiang Tian paper tracker

Last public-source sweep: **2026-08-26**.

This file separates the discovery queue from completed reproduction directories. It intentionally includes preprints and tool demonstrations that may not yet be prominent in Scholar/DBLP so they do not get lost between daily runs.

| Paper | Public status | Reproduction status |
|---|---|---|
| LPO: Discovering Missed Peephole Optimizations with Large Language Models | ASPLOS 2026 | ✅ `papers/2026-lpo/` |
| Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets | TOSEM 2026 | ✅ `papers/2026-thaliatype/` — L1 partial |
| Optimization-Aware Test Generation for Deep Learning Compilers | ICSE 2026 | ✅ `papers/2026-oatest/` |
| Bounded Exhaustive Random Program Generation for Testing Solidity Compilers | ICSE 2026 | ✅ `papers/2026-erwin/` |
| On the Feasibility of Deduplicating Compiler Bugs with Bisection | ISSTA 2026 | ✅ `papers/2026-buglens/` |
| Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types | ISSTA 2026 | ✅ `papers/2026-scitix/` |
| RepoTrace: Browser-Assisted Evidence Collection for GitHub Research Datasets | SPLASH/ISSTA 2026 Tool Demo | ⏳ pending |
| DebugTracker: Lightweight Process Evidence for Classroom Debugging | SPLASH/ISSTA 2026 Tool Demo | ⏳ pending |
| LPR+: Diverse Transformations for LLM-Aided Program Reduction | SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-lpr-plus/` — L0 + scoped L2 |
| TEMPLATEFUZZ: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs | arXiv 2604.12232, 2026-04-14 | ⏳ pending |
| DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction | arXiv 2605.19412, 2026-05-19 | ✅ `papers/2026-drreduce/` — scoped L1 + scoped L2 |
| CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers | arXiv 2606.28132 + SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-crosslangfuzzer/` |
| Delta Debugging in the Absence of Test Oracles Through Metamorphic Testing (DDMT) | arXiv 2607.00929, 2026-07-01 | ✅ `papers/2026-ddmt/` — scoped L1 + scoped L2 mechanism |
| Semantic-aware and Self-improving Program Reduction via Agentic Large Language Models (PROJ) | arXiv 2607.03766, 2026-07-04 | ✅ `papers/2026-proj/` |
| VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations | 2026 preprint | ✅ `papers/2026-vizdetour/` |
| Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries | DBLP: TOSEM 35(4), 2026; author page lists TOSEM 2025 | ⏳ pending — publication-year drift recorded |

## Discovery sources

- Yongqiang Tian publications: https://yqtian.com/pub.html
- Google Scholar / DBLP author records
- arXiv searches for newly indexed preprints
- conference publication pages and official artifacts/GitHub repositories

## Discovery note (2026-08-26)

No newer compiler/testing/program-reduction preprint dated after the already tracked July 2026 work was found in today's public-source sweep. The highest-priority pending compiler/code-reasoning-adjacent 2026 paper was therefore **Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets** (TOSEM 2026), which has now been added as an L1-partial reproduction.

The official `uw-pluverse/thalia-type` artifact is public and includes the benchmark data, transformations, saved SnR/Llama/GPT outputs and upstream metric implementation. Reprocessing is intentionally partial because the current public artifact snapshot does not expose the StarCoder2 result directories needed to recompute the two StarCoder2 Figure 7 cells.

## Next queue

1. **RepoTrace** — new 2026 tool demo; useful for evidence provenance in GitHub-based empirical research.
2. **DebugTracker** — new 2026 tool demo; process-evidence tooling.
3. **TEMPLATEFUZZ** — 2026 testing work, but lower priority for the compiler-focused track.
4. **Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries** — DBLP publication-year drift remains recorded; reproduce after higher-priority 2026 queue.

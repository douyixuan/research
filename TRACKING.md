# Yongqiang Tian paper tracker

Last public-source sweep: **2026-09-01**.

This file separates the discovery queue from completed reproduction directories. It intentionally includes preprints and tool demonstrations that may not yet be prominent in Scholar/DBLP so they do not get lost between daily runs.

| Paper | Public status | Reproduction status |
|---|---|---|
| LPO: Discovering Missed Peephole Optimizations with Large Language Models | ASPLOS 2026 | ✅ `papers/2026-lpo/` |
| Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets | TOSEM 2026 | ✅ `papers/2026-thaliatype/` — L1 partial |
| Rethinking LLM-aided RTL Code Optimization Via Timing Logic Metamorphosis | TRETS 2026 on yqtian.com; public arXiv v1 is 2025 and has older authorship | ✅ `papers/2026-rtl-timing-metamorphosis/` — L0 provenance audit + scoped L2 |
| Optimization-Aware Test Generation for Deep Learning Compilers | ICSE 2026 | ✅ `papers/2026-oatest/` |
| Bounded Exhaustive Random Program Generation for Testing Solidity Compilers | ICSE 2026 | ✅ `papers/2026-erwin/` |
| On the Feasibility of Deduplicating Compiler Bugs with Bisection | ISSTA 2026 | ✅ `papers/2026-buglens/` |
| Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types | ISSTA 2026 | ✅ `papers/2026-scitix/` |
| RepoTrace: Browser-Assisted Evidence Collection for GitHub Research Datasets | SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-repotrace/` — L0 artifact audit + scoped L2 |
| DebugTracker: Lightweight Process Evidence for Classroom Debugging | SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-debugtracker/` — L0 artifact audit + scoped L2 |
| LPR+: Diverse Transformations for LLM-Aided Program Reduction | SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-lpr-plus/` — L0 + scoped L2 |
| TEMPLATEFUZZ: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs | arXiv 2604.12232, 2026-04-14 | ✅ `papers/2026-templatefuzz/` — L0 artifact/interface audit + scoped L2 safe mechanism |
| DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction | arXiv 2605.19412, 2026-05-19 | ✅ `papers/2026-drreduce/` — scoped L1 + scoped L2 |
| CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers | arXiv 2606.28132 + SPLASH/ISSTA 2026 Tool Demo | ✅ `papers/2026-crosslangfuzzer/` |
| Delta Debugging in the Absence of Test Oracles Through Metamorphic Testing (DDMT) | arXiv 2607.00929, 2026-07-01 | ✅ `papers/2026-ddmt/` — scoped L1 + scoped L2 mechanism |
| Semantic-aware and Self-improving Program Reduction via Agentic Large Language Models (PROJ) | arXiv 2607.03766, 2026-07-04 | ✅ `papers/2026-proj/` |
| VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations | 2026 preprint | ✅ `papers/2026-vizdetour/` |
| Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries | ACM TOSEM 35(4), Article 88, Apr 2026; author page lists TOSEM 2025 | ✅ `papers/2026-dllens/` — L1 partial + L0 implementation audit |
| WDD: Weighted Delta Debugging | ICSE 2025; official Zenodo artifact v2 | ✅ `papers/2025-wdd/` — scoped L2 mechanism + official artifact demo CI |

## Discovery sources

- Yongqiang Tian publications: https://yqtian.com/pub.html
- Google Scholar / DBLP author records
- arXiv searches for newly indexed preprints
- conference publication pages and official artifacts/GitHub repositories

## Discovery note (2026-09-01)

A fresh sweep of Yongqiang Tian's publication page plus recent arXiv/DBLP-oriented searches did **not** surface a new 2026 paper/preprint beyond the items already tracked through 2026-08-31. The queue therefore moved backward to an unfinished high-priority program-reduction paper: **WDD: Weighted Delta Debugging (ICSE 2025)**.

WDD has an official Artifact Available/Functional package on Zenodo (`10.5281/zenodo.14301983`) containing source, 32 C + 30 XML benchmarks, scripts, raw result directories, and a documented Docker image. Today's scoped L2 implements the core weighted partitioning mechanism with a true/uniform/inverted-weight ablation, and CI additionally runs one official Perses ddmin/Wddmin C demo from the authors' Docker image. Full 62-case L3 and the 5-repeat ProbDD/WProbDD lanes remain intentionally outside default CI because the artifact documentation states that the complete experiments take very long.

## Next queue

Re-scan 2026 first. If no new item appears, continue with **Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction**, then **Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations**, then probabilistic-delta-debugging work.

# Yongqiang Tian paper tracker

Last public-source sweep: **2026-09-12**.

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
| Semantic-aware and Self-improving Program Reduction via Agentic Large Language Models (PROJ) | arXiv 2607.03766, 2026-07-04 | ✅ `papers/2026-proj/` — L0 claim audit + scoped L2 control mechanism; live-LLM lane scaffolded |
| VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations | 2026 preprint | ✅ `papers/2026-vizdetour/` |
| Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries | ACM TOSEM 35(4), Article 88, Apr 2026; author page lists TOSEM 2025 | ✅ `papers/2026-dllens/` — L1 partial + L0 implementation audit |
| Update from Hell: Can Coding Agents Survive Hidden Breakage in Dependency Upgrades? (DEPBENCH) | arXiv 2026 preprint | ✅ `papers/2026-depbench/` — L0 + scoped L2 |
| Latra: A Template-Based Language-Agnostic Transformation Framework for Effective Program Reduction | ASE 2025 | ✅ `papers/2025-latra/` — L1 partial + official L2 probe scaffold |
| Boosting Program Reduction with the Missing Piece of Syntax-Guided Transformations (SFC) | OOPSLA 2025 | ✅ `papers/2025-sfc/` — L1 |
| T-Rec: Fine-Grained Language-Agnostic Program Reduction Guided by Lexical Syntax | TOSEM 2025 | ✅ `papers/2025-trec/` — L0 + scoped L2 |
| Weighted Delta Debugging (WDD) | ICSE 2025 | ✅ `papers/2025-wdd/` — L1 partial + scoped L2 |
| Toward a Better Understanding of Probabilistic Delta Debugging (CDD) | ICSE 2025 | ✅ `papers/2025-cdd/` — L1 partial + scoped L2 |
| A Tale of Two DL Cities: When Library Tests Meet Compiler (OPERA) | ICSE 2025 | ✅ `papers/2025-opera/` — L1 + scoped L2 |
| LPR: Large Language Models-Aided Program Reduction | ISSTA 2024 | ✅ `papers/2024-lpr/` — L1 partial |
| On the Caching Schemes to Speed Up Program Reduction (RCC) | TOSEM 2023 | ✅ `papers/2023-rcc/` — L0 artifact audit + scoped L2 |
| Pushing the Limit of 1-Minimality of Language-Agnostic Program Reduction (Vulcan) | OOPSLA 2023 | ✅ `papers/2023-vulcan/` — L0 artifact/implementation audit + scoped L2 |
| Compilation Consistency Modulo Debug Information (CCMD / Dfusor) | ASPLOS 2023 | ✅ `papers/2023-ccmd/` — L0 artifact audit + scoped L2 |
| PPR: Pairwise Program Reduction | ESEC/FSE 2023 | ✅ `papers/2023-ppr/` — L0 artifact audit + official current-source scoped L2 + independent scoped L2 |

## Discovery sources

- Yongqiang Tian publications: https://yqtian.com/pub.html
- Google Scholar / DBLP author records
- arXiv searches for newly indexed preprints
- ACM/IEEE/conference publication pages
- official artifacts and GitHub repositories

## Discovery note (2026-09-12)

A fresh sweep of Yongqiang Tian's publication page, Monash profile, arXiv/DBLP indexing, and targeted searches did not surface a new untracked 2026 compiler/testing/program-reduction paper that should preempt the queue. The next highest-value unfinished program-reduction paper was **PPR: Pairwise Program Reduction (ESEC/FSE 2023)**.

PPR is now reproduced at **L0 + scoped L2**, not L1/L3. The official source and Benchmark-PPR are public in `uw-pluverse/perses`, and the paper artifact is indexed at Zenodo `10.5281/zenodo.8267114`. A fresh compile/execute pairwise-reduction probe reduced a three-change variant difference to one critical changed-statement proxy, while a separate CI lane built and ran the current official PPR implementation from pinned Perses source. Paper-scale historical results were not rerun.

## Next queue

Re-scan 2026 first. If nothing new appears, continue backward through unfinished compiler/testing work. High-value candidates are **Ad Hoc Syntax-Guided Program Reduction (ESEC/FSE 2023 Tool)**, **Revisiting the Evaluation of Deep Learning-Based Compiler Testing (IJCAI 2023)**, and **Fuzzing Deep Learning Compilers with HirGen (ISSTA 2023)**.

# Yongqiang Tian paper tracker

Last public-source sweep: **2026-08-29**.

This file separates the discovery queue from completed reproduction directories. It intentionally includes preprints and tool demonstrations that may not yet be prominent in Scholar/DBLP so they do not get lost between daily runs.

| Paper | Public status | Reproduction status |
|---|---|---|
| LPO: Discovering Missed Peephole Optimizations with Large Language Models | ASPLOS 2026 | ✅ `papers/2026-lpo/` |
| Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets | TOSEM 2026 | ✅ `papers/2026-thaliatype/` — L1 partial |
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
| Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries | DBLP: TOSEM 35(4), 2026; author page lists TOSEM 2025 | ⏳ pending — publication-year drift recorded |

## Discovery sources

- Yongqiang Tian publications: https://yqtian.com/pub.html
- Google Scholar / DBLP author records
- arXiv searches for newly indexed preprints
- conference publication pages and official artifacts/GitHub repositories

## Discovery note (2026-08-29)

A fresh sweep of Yongqiang Tian's publication page and recent arXiv indexing did not expose a newer 2026 compiler/testing/program-reduction paper beyond the already tracked July work. The author page currently lists the 2026 formal publications and tool demos already represented above; TEMPLATEFUZZ remains a 2026 arXiv preprint rather than an item on that formal publication list.

Today's TEMPLATEFUZZ audit follows arXiv v1 (`2604.12232`, submitted 2026-04-14). The paper declares an anonymous 4open artifact. A separately discoverable public GitHub repository (`FFchopon/TemplateFuzz-LLM`, pinned here at `c1a11268139ceaaca659bc61346bc843ab1cf874`) matches the paper's M1–M5 mutation families and experiment interface, but the paper does not establish provenance equivalence between the two URLs. Therefore today's result is labeled L0 artifact/interface audit + scoped L2 safe mechanism, not L1. The CI reproduction intentionally uses only benign synthetic templates and no live jailbreak prompts or model endpoints.

## Next queue

1. **Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries** — DBLP/ACM publication-year drift remains recorded; reproduce next unless a newer 2026 paper/preprint appears.

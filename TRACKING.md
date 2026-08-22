# Yongqiang Tian paper tracker

Last public-source sweep: **2026-08-22**.

This file separates the discovery queue from completed reproduction directories. It intentionally includes preprints that have not yet appeared on the author's publication page so they do not get lost between daily runs.

| Paper | Public status | Reproduction status |
|---|---|---|
| LPO: Discovering Missed Peephole Optimizations with Large Language Models | ASPLOS 2026 | ✅ `papers/2026-lpo/` |
| Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets | TOSEM 2026 | ⏳ pending |
| Optimization-Aware Test Generation for Deep Learning Compilers | ICSE 2026 | ✅ `papers/2026-oatest/` |
| Bounded Exhaustive Random Program Generation for Testing Solidity Compilers | ICSE 2026 | ✅ `papers/2026-erwin/` |
| On the Feasibility of Deduplicating Compiler Bugs with Bisection | ISSTA 2026 | ✅ `papers/2026-buglens/` |
| Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types | ISSTA 2026 | ✅ `papers/2026-scitix/` |
| TEMPLATEFUZZ: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs | arXiv 2604.12232, 2026-04-14 | ⏳ pending |
| DRReduce: Enhancing Syntax-Guided Program Reduction with Dependency Reconstruction | arXiv 2605.19412, 2026-05-19 | ⏳ pending — high priority (program reduction) |
| CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers | arXiv 2606.28132, 2026-06-26 | ✅ `papers/2026-crosslangfuzzer/` |
| Semantic-aware and Self-improving Program Reduction via Agentic Large Language Models (PROJ) | arXiv 2607.03766, 2026-07-04 | ✅ `papers/2026-proj/` |
| VIZDETOUR: Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations | 2026 preprint | ✅ `papers/2026-vizdetour/` |

## Discovery sources

- Yongqiang Tian publications: https://yqtian.com/pub.html
- DBLP author record: https://dblp.org/pid/180/5774-1.html
- arXiv/DBLP searches for newly indexed preprints
- conference publication pages and official artifacts

## Next queue

1. **DRReduce** — directly aligned with compiler/program-reduction work and has quantitative ablations on dependency reconstruction.
2. **Unmasking the Type Inference Capabilities of LLMs for Java Code Snippets** — natural follow-up to Scitix and useful for comparing symbolic vs LLM inference.
3. **TEMPLATEFUZZ** — important testing work, but lower priority for the compiler-focused track.

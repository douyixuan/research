# CrossLangFuzzer: Differential Testing of Cross-Language JVM Compilers

Paper: Xiaotian Ma, Qiong Feng, Yongqiang Tian, Wei Song, Peng Liang. arXiv:2606.28132v1, 26 June 2026.

- Paper: https://arxiv.org/abs/2606.28132
- Official artifact: https://github.com/XYZboom/CrossLangFuzzer
- Archived artifact: https://doi.org/10.5281/zenodo.20925432
- Bug corpus: https://github.com/XYZboom/CrossLangFuzzerData

## TL;DR

The key idea is to move compiler fuzzing above any one source language. CrossLangFuzzer builds a language-agnostic JVM-oriented IR, generates a structurally valid program once, assigns declarations to Kotlin/Java/Groovy/Scala, mutates semantic pressure points, then differentially compiles the emitted multilingual program. This targets the interoperability boundary rather than each frontend in isolation.

The 2026 paper reports **32 confirmed compiler bugs**: 15 Kotlin, 4 Groovy, 7 Scala 3, 2 Scala 2, and 4 Java. The artifact also contains automatic IR reduction for bug-triggering programs.

## What is reproduced here

**Current level: L2 — live-minimal, scoped to one reported compiler bug.**

This is *not* an L2 reproduction of the full fuzzing search. It is a fresh end-to-end reproduction of one paper finding, KT-74109:

1. reconstruct the minimized mixed Java/Kotlin inheritance case from the authors' bug corpus;
2. compile the equivalent all-Java inheritance with `javac` as a language-boundary oracle;
3. compile the Kotlin subclass with the paper-era Kotlin compiler 2.1.0 and require the reported false rejection;
4. compile the same fixture with the current stable Kotlin 2.4.10 to measure toolchain drift;
5. record compiler diagnostics and results as a GitHub Actions artifact.

This validates that the reported finding is executable evidence rather than only a copied table, while explicitly avoiding the stronger claim that we rediscovered the bug through fuzzing.

Run locally:

```bash
bash papers/2026-crosslangfuzzer/reproduce.sh
cat papers/2026-crosslangfuzzer/results/summary.md
```

Requirements: Linux/macOS, JDK 17, `curl`, `unzip`, and `sha256sum`/`shasum`. Kotlin compiler distributions are downloaded from JetBrains releases and checksum-verified.

## Architecture reconstructed from the paper/artifact

```text
configuration
    |
    v
IR generator -- structural/type constraints --> valid unified IR
    |
    +--> weighted semantic mutations
    |      - generic arguments / bounds
    |      - nullability
    |      - override structure
    |      - language shuffling
    v
language printers
    +--> Kotlin
    +--> Java / Groovy
    +--> Scala
    |
    v
compiler runners
    +--> normal test: crash/internal error
    +--> differential test: accept/reject or behavior mismatch
    |
    v
candidate bug --> IR DDMin reducer --> minimized report --> developer confirmation
```

The important research choice is the **unified semantic IR**. Language placement becomes a mutation dimension: the same class hierarchy can be re-expressed across language boundaries while preserving a shared structural representation.

## Paper claims vs this reproduction

| Claim | Paper evidence | Evidence here | Status |
|---|---|---|---|
| Cross-language boundaries expose bugs missed by isolated frontend testing | 32 confirmed bugs across five JVM compilers | KT-74109 mixed Java/Kotlin trigger is compiled live | partial support |
| CrossLangFuzzer found 15 Kotlin bugs | developer-confirmed issue table | one selected Kotlin finding rerun | not reproduced at scale |
| Generated tests use a unified IR and language-specific printers | design + open-source implementation | source/artifact structure audited | structural support |
| Seven mutations diversify semantic interactions | design table + implementation | source/artifact structure audited | structural support |
| Automatic IR reduction produces actionable minimized failures | reducer design + `out/min` reports | authors' minimized KT-74109 is used; reduction itself not rerun | not yet reproduced |
| Total = 32 confirmed bugs | issue table and developer validation | no independent 32-bug confirmation campaign | not reproduced at scale |

## Why KT-74109 is a useful minimal experiment

The trigger stresses default-method resolution across a Java/Kotlin boundary. Java accepts the inheritance graph because the inherited final concrete method resolves the interface implementations. The affected Kotlin compiler rejects the Kotlin subclass as if it still had to override `func` due to multiple inherited implementations.

This gives a clean differential oracle: **same JVM inheritance semantics, Java subclass accepted, Kotlin subclass rejected**. It directly tests the kind of semantic boundary CrossLangFuzzer is designed to explore.

## Experimental design for this L2 lane

Independent variable:

- compiler frontend/version: `javac 17`, Kotlin 2.1.0, Kotlin 2.4.10.

Controlled input:

- identical Java hierarchy and final Kotlin subclass shape reconstructed from the minimized report.

Oracles:

- Java equivalent must compile;
- Kotlin 2.1.0 must reject and emit a diagnostic consistent with the reported multiple-implementation bug;
- Kotlin 2.4.10 is observational: pass means the bug no longer reproduces in current stable; reject means it survives toolchain drift.

Outputs:

- exact exit codes;
- compiler diagnostics;
- a generated Markdown summary uploaded by CI.

## Threats / limitations

1. **Selection bias.** We start from a known minimized trigger, so this validates a finding but says nothing about rediscovery probability.
2. **No generator/mutator execution yet.** The fuzzer search loop, mutation distribution, and reducer are outside this L2 slice.
3. **Version drift.** The open-source artifact has continued evolving after the paper; the full-scale lane must pin the Zenodo snapshot or a paper-era commit.
4. **Environment drift.** JDK/library versions can affect JVM-language interoperability. CI pins JDK 17 but does not reproduce every historical toolchain component.
5. **Confirmation is not re-adjudicated.** We rely on the public developer-confirmed issue set rather than independently classifying all 32 reports.
6. **One bug class.** KT-74109 exercises override resolution; it does not cover generics, nullability, bytecode mismatches, crashes, or other languages.

## Highest-value extensions

### 1. Compiler-version survival matrix — first priority

Run every minimized bug across historical -> current compiler releases and classify:

`introduced -> exposed -> fixed -> regressed`

This turns a one-time bug count into a **bug survival curve** and answers whether findings remain useful as toolchains evolve. The current 2.1.0 vs 2.4.10 check is the first cell of that matrix.

### 2. Semantic-boundary coverage

Raw branch coverage can hide why cross-language generation helps. Instrument frontend subsystems specifically responsible for inheritance resolution, type substitution, nullability/platform types, bridge methods, and metadata loading. Compare:

`single-language fuzzing vs cross-language IR fuzzing`

on boundary-specific coverage and unique confirmed bugs per covered boundary.

### 3. Hold structure fixed, shuffle only language assignment

A particularly clean ablation is:

`same IR graph + same types + same declarations`, change only declaration language placement.

Measure which boundaries flip compiler outcomes. This isolates the causal value of language interoperability from general program diversity.

### 4. Post-paper unseen-version campaign

Run on compiler releases after the paper's June 2026 snapshot. This reduces the risk that evaluation is overfitted to already-known bug patterns and provides a stronger prospective test.

### 5. Cost-normalized baseline

Compare against a single-language generator using equal CPU time and compiler invocations, then report:

- time-to-first confirmed bug;
- unique confirmed bugs / 1k compilations;
- unique root causes / CPU-hour;
- reducer time and minimized size.

Bug count alone is too sensitive to campaign budget and duplicate clustering.

### 6. LLM-guided IR mutation

The paper explicitly leaves LLM manipulation of serialized IR as future work. A useful extension is to let an LLM propose mutation *operators or regions*, while preserving a deterministic validator and compiler oracle. Compare against the weighted random mutator on boundary coverage and unique root causes, not merely crash count.

## Path to L3

See [L3_PLAN.md](L3_PLAN.md). L3 requires running the actual generator/mutator/runner/reducer pipeline at paper-like scale and independently reconstructing a meaningful subset of the reported bug campaign; rerunning known triggers alone does not qualify.

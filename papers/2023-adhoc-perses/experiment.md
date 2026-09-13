# Experiment design

## Question

Can the public, current Perses implementation still perform the paper's central ad-hoc workflow: take an unseen ANTLR grammar plus a small YAML language description, generate a language-support JAR without editing/rebuilding Perses source for that language, and then use that JAR to reduce a property-preserving input?

## Scoped L2 protocol

1. Pin upstream `uw-pluverse/perses` at `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2`.
2. Build the official ad-hoc installer and official Perses deploy JARs from that source.
3. Supply a repository-local ANTLR4 grammar for an intentionally unsupported `Tiny` language and a YAML language-kind file.
4. Generate `tiny-language.jar` with the official installer.
5. Reduce a four-statement Tiny program with the official Perses binary plus `--language-ext-jars tiny-language.jar`.
6. The deterministic property oracle requires the lexical markers `bug` and `keep` to survive.
7. Assert the reduced program still preserves the property and is smaller than the input. Save build/install/reduction logs, environment metadata, JAR checksum and metrics as a GitHub Actions artifact.

This is a **fresh minimal end-to-end mechanism reproduction (L2)** against current public source. It is not L1 because it does not recompute the paper's released evaluation table, and it is not L3 because it does not rerun the paper-scale benchmark suite or historical environment.

## Paper comparison

The paper's main usability claim is that support for a new context-free-grammar language can be added using configuration + one installer command rather than manually normalizing the grammar, integrating language-specific infrastructure into Perses, and rebuilding a bespoke Perses binary. It reports a GLSL case-study reduction from roughly 190 lines of support code to roughly 20 and reports ad-hoc reduction effectiveness/efficiency comparable with normal Perses, with language-installation overhead on the order of seconds.

This reproduction tests the same control path but on a new Tiny grammar. It deliberately does **not** compare its tiny timing to the paper's timing as a performance replication: current source, current Bazel/JDK, GitHub-hosted hardware, grammar size and cold-build effects differ materially.

## Threats and limitations

- Current Perses source may have evolved materially since the 2023 paper; this is a toolchain-drift probe, not the paper artifact environment.
- One tiny grammar only establishes that the mechanism works end to end; it says nothing about grammar complexity, semantic predicates, split lexer/parser grammars, generated base classes or large-language robustness.
- Wall-clock measurements include noisy hosted-runner effects and are descriptive only.
- The property is lexical and deterministic, so it does not approximate a real compiler crash or miscompilation oracle.
- No historical Perses-vs-Perses-ad-hoc benchmark results are recomputed, so no paper-scale effectiveness claim is reproduced.

## Promotion path

- **L1:** obtain the exact 2023 result tables/artifact inputs and rerun their analysis to recompute published size/runtime comparisons.
- **L3:** pin the paper-era Perses/Java/Bazel environment and rerun all paper subjects, including GLSL, with repeated timings.
- **L4:** evaluate grammar/toolchain drift across historical and current ANTLR/Perses versions and several previously unsupported languages.

## Highest-value extension

Build a **grammar-complexity × toolchain-drift matrix**. For each of several unseen languages (small DSL, GLSL-like grammar, split lexer/parser grammar, grammar with semantic predicates), run paper-era and current Perses ad-hoc installation and reduction under a fixed oracle budget. Measure installation success, generated-JAR size, parser-build time, reduction result size, query count and failure category. This tests whether the paper's usability result survives modern grammar/toolchain drift rather than merely showing that the happy path still works.

# Experiment design

## Questions

**H1 — Published-output consistency.** Reprocessing the immutable public CSV snapshot should reproduce Latra's headline token-effectiveness claims: 33.77% mean per-subject improvement over Vulcan for C and 9.17% for SMT-LIB, with paper-rounded final-token means of 89/85 (Latra/C-Reduce) and 103/109 (Latra/ddSMT).

**H2 — Mechanism survival under source drift.** The current pinned Perses/Latra source should still build and pass representative upstream C, SMT, and general matcher/rewriter tests.

H1 is **L1** evidence. H2 is a **scoped L2** mechanism probe. Neither establishes paper-scale L3 reproduction.

## Inputs and pins

- official artifact: `uw-pluverse/latra-artifact@7a9e619b74c11418f5c5d9b469227153b674d8a5`
- current Perses source: `uw-pluverse/perses@6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2`
- Bazelisk: `v1.29.0`; the Perses checkout selects Bazel through its checked-in `.bazelversion`

## L1 procedure

1. Fetch the official artifact at the exact commit.
2. Load `c-benchmark.csv`, `smt-tokens.csv`, `smt-queries.csv`, and `smt-time.csv`.
3. Verify 20 C and 205 SMT subjects and aligned subject IDs across the SMT tables.
4. Recompute per-subject relative token improvement as `(Vulcan - Latra) / Vulcan * 100`, then take the arithmetic mean across subjects.
5. Recompute arithmetic mean final token counts.
6. Run an exact paired sign test for Latra vs C-Reduce on the C token table as a transparent secondary check.
7. Emit a JSON report and fail if headline values drift from the published figures.

## Scoped L2 procedure

Build the pinned modern Perses source and execute:

- `FullFunctionalLatraRewriterBuilderTest`
- `CLatraTransformationTest`
- `SMTLatraTransformationTest`

These tests exercise the live Latra matcher/rewriter and language-specific transformations without pretending to be the 225-subject evaluation.

## Metrics

L1: subject count, mean final tokens, mean per-subject relative token improvement, exact paired sign-test result, and basic query/time summaries.

L2: build/test pass/fail plus the exact source/tool version pins.

## Promotion criteria

- **L1 partial:** published CSVs are successfully parsed and headline figures reproduced.
- **scoped L2:** fresh pinned-source tests pass in CI.
- **L3:** all 225 subjects are rerun from inputs using immutable paper-compatible binaries/environment; fresh Table 2/Figure 4 values are regenerated, with repeated timing trials.
- **L4:** execute the toolchain-drift/template-ablation matrix described in the technical README.

## Known blocker for L3

The public artifact instructions use `cancel/latra-artifact:latest` for the full benchmark/binary environment. The public GitHub repository contains summary CSVs/scripts rather than the complete benchmark/binary bundle, and the README does not publish an immutable paper-era Docker digest. A long paper-scale run is also explicitly described as resource-intensive and sensitive to timeout effects under CPU oversubscription.

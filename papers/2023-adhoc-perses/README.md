# Ad Hoc Syntax-Guided Program Reduction

Jia Le Tian, Mengxiao Zhang, Zhenyang Xu, Yongqiang Tian, Yiwen Dong, Chengnian Sun. ESEC/FSE 2023 Tool Demonstrations. DOI: 10.1145/3611643.3613101.

## Core idea

Perses is language-agnostic at the reduction-algorithm level, but historically adding a new language still required transforming its ANTLR grammar, writing parser/language integration code, editing Bazel targets, rebuilding Perses, and maintaining that integration. Perses-adhoc moves this boundary into a runtime extension mechanism: an ANTLR grammar plus a small YAML language description is compiled into a loadable JAR, then ordinary Perses loads it through `--language-ext-jars`.

The research contribution is therefore less a new reducer than a **packaging/interface change that makes syntax-guided reduction deployable for arbitrary grammars without modifying the Perses source tree**.

## Paper claims used as references

The paper evaluates five GCC/Clang bugs and reports identical final token counts for native Perses and Perses-adhoc on all five: `98, 144, 153, 328, 51` tokens (mean 154.8, printed as 155), from inputs averaging 29,764 tokens.

For the same five subjects, the printed runtimes average 1191.4 s for native Perses and 1221.6 s for Perses-adhoc, i.e. **2.535% overhead** when recalculated from the table. Mean printed throughput is 43.048 vs 41.828 tokens/s. Grammar-to-extension generation for JSON/C/Scala/Rust/C++/Java averages **10.754 s**, with Java the slowest printed case at 15.672 s.

These are reference-paper arithmetic checks only. This directory does **not** call them L1 because the historical released result files were not reprocessed.

## Reproduction level

**Current target level: L0 official implementation audit + official current-source scoped L2.**

- **L0:** the current official Perses source still contains the ad-hoc installer, documentation, and a dedicated system test for generation/loading/reduction.
- **Scoped L2:** GitHub Actions runs the unmodified official current-source system-test target from pinned Perses commit `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2`.
- **Not L1:** `recompute_claims.py` uses numbers transcribed from the paper, not historical artifact outputs.
- **Not L3:** the five historical GCC/Clang bug experiments and paper-era toolchains are not rerun.
- **Not L4:** the proposed modern-language/toolchain-drift matrix is designed but not executed here.

The L2 label is valid only if the official CI lane passes; the workflow logs and artifact are the evidence.

## Run

Fast deterministic claim audit:

```bash
cd papers/2023-adhoc-perses
RUN_OFFICIAL=0 ./reproduce.sh
```

Full current-source probe:

```bash
./reproduce.sh
```

The official lane clones the pinned Perses commit and runs:

```bash
bazelisk test //test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing \
  --test_output=all --test_timeout=1200
```

## What the official scoped L2 actually tests

The upstream Perses test performs the mechanism end to end rather than mocking it:

1. build/use the official ad-hoc grammar installer;
2. compile the C ANTLR grammar plus language YAML into an extension JAR;
3. create a fresh file containing `int var = 0;`;
4. use an interestingness test that requires `var` to remain;
5. invoke Perses with `--language-ext-jars`;
6. verify the reduced result no longer contains `int`.

A passing lane therefore demonstrates that the paper's dynamic grammar-installation path still executes in current Perses. It does **not** establish paper-scale effectiveness or performance equivalence.

## Paper vs reproduction

| Aspect | Paper | This reproduction |
|---|---|---|
| language integration | ad-hoc JAR generated from grammar + YAML | same official current-source mechanism |
| reduction subjects | 5 historical GCC/Clang bugs | 1 tiny fresh upstream system-test case |
| final-size comparison | native and ad-hoc equal on all 5 subjects | mechanism pass/fail only |
| performance | mean 1191.4 s vs 1221.6 s from printed table | no paper-comparable runtime claim |
| grammar generation | six grammars, mean 10.754 s from printed table | current build/test executed, not treated as comparable generation benchmark |
| evidence level | paper-scale experiment | L0 + scoped L2 when CI passes |

## Threats and limitations

1. The pinned source is from 2026, not the paper-era Perses revision; ANTLR, Bazel, JDK, reduction passes, and parser handling have drifted.
2. The official system test is intentionally tiny and synthetic. It verifies dynamic installation and reduction, not compiler-bug reduction quality.
3. A successful current-source test cannot show the paper's native-vs-ad-hoc final-size equivalence or 2.6% runtime overhead.
4. Cold Bazel build time must not be compared with the paper's grammar-generation timings.
5. The paper uses slightly different wording around the amount of manual integration code (roughly 190/200 lines); this reproduction treats that as descriptive rather than a metric to reproduce.
6. The arithmetic audit is useful for catching transcription/aggregation inconsistencies but is not independent experimental evidence.

## Most useful next experiment (L4)

**Modern grammar onboarding × toolchain drift.** Choose several current grammars not natively supported by Perses and compare dynamic ad-hoc integration with static/native integration under a fixed oracle budget. Measure setup LOC/configuration, installation/build time, parser compatibility, final tokens, oracle calls, wall-clock time, and failure categories across multiple Perses/ANTLR/JDK versions.

For compiler work, a particularly useful variant is a modern DSL such as WGSL or an MLIR-like textual subset. It tests whether the original benefit survives today's toolchain and whether ad-hoc grammar integration changes reduction quality when grammars contain modern lexer modes, semantic predicates, generated actions, or unusual token channels.

## Upgrade path

- **L1:** obtain and reprocess released historical experiment result files/logs for Tables 2-4 rather than transcribing paper values.
- **L3:** reconstruct the five GCC/Clang subjects, exact interestingness tests, compiler versions, and paper-era Perses environment; rerun at paper-like budgets.
- **L4:** execute the modern grammar/toolchain-drift experiment above with repeated runs and failure classification.

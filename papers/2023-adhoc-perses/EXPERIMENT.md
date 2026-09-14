# Experiment design

## Questions

1. Does the current official Perses source still support the paper's ad-hoc grammar path end to end: grammar + YAML -> extension JAR -> dynamic loading -> syntax-guided reduction?
2. Are the headline arithmetic claims in Tables 2-4 internally consistent?
3. What evidence is still missing for historical paper-scale reproduction?

## H1 — current-source end-to-end mechanism

Run the official Perses target:

```bash
bazelisk test //test/org/perses/adhoc:system_test_of_adhoc_fuzz_testing --test_output=all
```

The upstream test itself generates an extension language JAR from `OrigC.g4` plus YAML, creates a fresh source file `int var = 0;`, loads the extension through `--language-ext-jars`, preserves an oracle requiring `var`, and checks that the reduced result no longer contains `int`.

Success criterion: the unmodified upstream test passes from a clean pinned checkout. This is an **official current-source scoped L2** because a fresh end-to-end experiment runs, but it is not a historical compiler-bug reproduction.

## H2 — paper-claim arithmetic audit

`recompute_claims.py` recalculates values transcribed from Tables 2-4:

- Table 2: equality of Perses vs Perses-adhoc final token counts and means;
- Table 3: mean runtime, mean throughput, and relative runtime overhead;
- Table 4: mean/max grammar-generation time.

This is **not L1**. The inputs are values printed in the paper, not released historical experiment outputs.

## Outputs

- `results/paper_claims.json` — deterministic claim arithmetic;
- `results/official/official-system-test.log` — official Bazel test output;
- `results/official/bazel-test.log` — upstream test log when Bazel exposes it;
- `results/official/summary.txt` — pinned commit/toolchain/status metadata.

GitHub Actions uploads both result groups as artifacts.

## Historical L3 requirements

A paper-scale rerun requires the five historical GCC/Clang bug subjects and their exact interestingness tests, paper-era compiler binaries/configurations, a compatible paper-era Perses/Java/Bazel environment, and enough CPU time for runs on the order of the paper's ~20-minute mean per subject. The current-source test intentionally does not substitute for those requirements.

## Proposed L4

Run a toolchain-drift/onboarding matrix over modern ANTLR grammars that are not built into Perses. Compare dynamic ad-hoc installation against static/native integration on setup LOC, install/build latency, parse compatibility, final reduced size, oracle calls, wall-clock time, and failure categories. A compiler-oriented variant should include a current DSL such as WGSL or an MLIR-like textual grammar and repeat across Perses/ANTLR/JDK versions to expose grammar and toolchain drift.

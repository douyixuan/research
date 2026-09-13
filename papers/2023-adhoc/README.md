# Ad Hoc Syntax-Guided Program Reduction (ESEC/FSE 2023 Tool)

Paper: https://doi.org/10.1145/3611643.3613101  
Author PDF: https://cs.uwaterloo.ca/~cnsun/public/publication/fse23-tool/fse23-tool.pdf  
Official implementation: https://github.com/uw-pluverse/perses  
Current documentation: https://github.com/uw-pluverse/perses/blob/master/doc/install_new_languages.md

## Core insight

Perses is language-agnostic at the reduction-algorithm level, but historically adding a language still required users to normalize an ANTLR grammar, edit Perses integration/build code, and rebuild Perses. `Perses^ad_hoc` moves this boundary: an `AdhocCompiler` takes an ANTLR grammar plus a small YAML language description, generates a language-support JAR, and Perses dynamically loads that JAR through `--language-ext-jars`.

The paper therefore makes a usability claim as much as a reduction claim: dynamic grammar integration should preserve Perses reduction behavior while removing most language-integration engineering.

## Paper claims checked

From the paper tables/text:

- GLSL integration: the table lists 89 + 3 + 67 + 33 = **192** lines of Perses-side integration code; the paper describes this approximately as 190/200 lines and reports roughly 20 lines with the ad-hoc path.
- Effectiveness (Table 2): on five C compiler bugs, native Perses and ad-hoc C support reduce to the **same final token count** on every subject (mean 155 tokens).
- Efficiency (Table 3): native Perses mean 1,191 s vs ad-hoc mean 1,222 s, reported as about **2.6% overhead**.
- Grammar-library generation (Table 4): six grammars take 2.483–15.672 s; the printed values average **10.754 s**, consistent with the paper's “around 10 seconds”.

`audit_claims.py` rechecks only the arithmetic printed in the paper. This is **L0 claim audit**, not L1: no released raw experiment output is being reprocessed.

## Current artifact audit

Pinned current upstream commit used by the live probe:

`6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2` (2026-08-27)

The current tree still contains:

- `src/org/perses/grammar/adhoc/` implementation,
- `doc/install_new_languages.md`,
- an upstream end-to-end ad-hoc system test that generates an extension JAR and reduces a C-like test file using `--language-ext-jars`.

One important 2026 packaging drift: Perses v2.7 releases `perses_deploy.jar`, `kitten_deploy.jar`, and `kitten_organizer_deploy.jar`, but **does not publish the ad-hoc installer JAR as a release asset**. The current installation documentation therefore starts by building `perses_adhoc_installer_deploy.jar` from source. Functionality remains present, but the release-only “black-box” user path is less complete than the paper's usability framing suggests.

## Reproduction level

**Target: L0 + scoped L2 current-source. Not L1 and not L3.**

`reproduce.sh` performs a real end-to-end probe against the pinned current Perses source:

1. build the official Perses binary and ad-hoc grammar installer;
2. generate a language-support JAR from Perses' C ANTLR grammar plus the official ad-hoc test YAML;
3. reduce `int var = 0;` through that dynamically loaded grammar JAR while preserving an oracle that requires `var`;
4. run the same tiny input through native C support;
5. save both reduced programs, byte/token proxies, JAR hash, grammar-generation time, and logs.

This directly tests the mechanism and a tiny native-vs-ad-hoc comparison. It does **not** reproduce the five historical compiler bugs, paper-scale timings, or historical environment.

## Experiment design

Hypothesis H1: the current AdhocCompiler can still generate a loadable language JAR from an ANTLR grammar without modifying Perses source.

Hypothesis H2: Perses can consume the generated JAR and perform syntax-guided reduction while preserving the supplied property.

Hypothesis H3 (scoped): on the same tiny C input and oracle, native and ad-hoc grammar paths should reach comparable reduced results. Any difference is recorded rather than silently treated as failure.

The CI uses Ubuntu 24.04, Temurin JDK 21, Bazelisk, and `clang-format`. Cold Bazel build time is deliberately not compared to the paper's grammar-generation time.

## Paper vs reproduction

| Claim | Paper | This reproduction | Status |
|---|---:|---|---|
| Dynamic grammar support works | Grammar + YAML -> JAR -> Perses | Real current-source build/JAR/reduction | scoped L2 |
| Native vs ad-hoc effectiveness | identical token counts on 5 real bugs | tiny C case only | scoped L2, not paper-scale |
| Mean reduction time | 1191 s vs 1222 s | not rerun | not reproduced |
| Grammar generation | ~10 s average over 6 grammars | one current C grammar, recorded but not directly comparable | toolchain-drift probe |
| GLSL integration effort | ~190/200 -> ~20 LOC | paper arithmetic audited only | L0 |

## Threats and limitations

- The live case is intentionally tiny and does not approximate the five historical GCC/Clang bugs.
- Current Perses (2026) includes years of implementation and toolchain drift relative to the 2023 evaluation.
- Java/Bazel/ANTLR and host hardware differ, so generation/reduction timing is not directly comparable.
- The paper's benchmark inputs/raw timing outputs are not packaged as a standalone artifact here; therefore this work does not claim L1.
- The current probe uses the official C grammar for the extension JAR. It validates the ad-hoc machinery but is not evidence for every arbitrary grammar.

## Blockers to higher levels

To reach **L1**, obtain/recover the released raw logs/results for the five Table-2/Table-3 compiler bugs and reprocess them independently.

To reach **L3**, pin the paper-era Perses/AdhocCompiler revision, historical compiler versions and five bug-triggering programs/oracles, then rerun native and ad-hoc variants under a controlled machine image with repeated timing trials.

## Research extension / L4 proposal

### Packaging and toolchain-drift study

Re-evaluate the paper's *usability* claim, not only reduction quality:

- paper-era Perses vs current Perses v2.7/current source;
- release-only install vs source-build install;
- cold build, warm build, and grammar-JAR-generation-only time;
- C/Rust/Java/Scala/JSON plus a modern grammar not built into Perses;
- native vs ad-hoc final tokens, oracle calls, wall time, JAR generation time, peak RSS, and setup steps;
- JDK/Bazel version ablation.

The most actionable baseline is a release that also ships `perses_adhoc_installer_deploy.jar`. If that removes the source-build dependency without changing reduction behavior, it is a concrete modern improvement to the original tool's usability contract.

## Run

Quick arithmetic audit:

```bash
python3 papers/2023-adhoc/audit_claims.py
```

Full current-source scoped L2:

```bash
bash papers/2023-adhoc/reproduce.sh
```

Results are written under `papers/2023-adhoc/results/` and uploaded by GitHub Actions.
# Ad Hoc Syntax-Guided Program Reduction

Paper: Jia Le Tian, Mengxiao Zhang, Zhenyang Xu, Yongqiang Tian, Yiwen Dong, Chengnian Sun. **Ad Hoc Syntax-Guided Program Reduction.** ESEC/FSE 2023 Demonstrations. DOI: 10.1145/3611643.3613101.

Official implementation: `uw-pluverse/perses`, especially `src/org/perses/grammar/adhoc/` and `doc/install_new_languages.md`.

## Core idea

Classic Perses is language-agnostic in its reducer, but historically adding a new language still required normalizing the ANTLR grammar, editing Perses integration code, and rebuilding Perses. `Perses^adhoc` moves that integration step into an `AdhocCompiler`: a grammar plus a small YAML language description is compiled into a loadable JAR, which stock Perses can then load dynamically with `--language-ext-jars`.

The paper's main usability claim is therefore not a new minimization algorithm; it is **dynamic language onboarding without editing/rebuilding the Perses codebase for each new grammar**.

## Paper claims used as references

- GLSL integration code drops from about **190 lines to 20 lines**.
- On five C compiler-bug subjects, native Perses and `Perses^adhoc` produce the **same final token counts** (mean 155 tokens).
- Mean reduction time is **1,191 s native vs 1,222 s adhoc**, about **2.6% slower** for the dynamic path in that experiment.
- Grammar-library generation takes roughly **2.5–15.7 s** for the six reported languages, around 10 s on average.

These are paper results only. This directory does not label them as reproduced unless an experiment below actually recomputes them.

## Reproduction level

**Current level: L0 artifact/implementation audit + scoped L2 current-source live-minimal.**

This is **not L1**: the five released compiler-bug experiments and Table 2/3 aggregates are not being reprocessed here.

This is **not L3**: the paper-scale C benchmark suite is not being rerun.

The scoped L2 lane uses the current Perses source pinned by commit, builds the official ad-hoc grammar compiler, compiles a previously unsupported toy language grammar into a language-extension JAR, dynamically loads it into the official Perses reducer, and reduces a real input under a property oracle.

## Experiment design

The tiny language `MiniCalc` has two statement forms:

```text
let <identifier> = <integer>;
print <identifier>;
```

The input has five statements. The oracle requires the two semantically important statements `let target = 7;` and `print target;` to remain. The other three assignments are removable.

The official current-source experiment performs the exact integration path described by the paper:

1. build `perses_adhoc_installer_deploy.jar` and `perses_deploy.jar`;
2. compile `MiniCalc.g4` + `language_kind.yaml` into `minicalc.jar`;
3. invoke Perses with `--language-ext-jars minicalc.jar`;
4. check that the reduced result still passes the property oracle;
5. require the five-statement input to reach exactly two statements;
6. save installer/reducer logs, environment information, and summary output under `results/`.

Run:

```bash
bash papers/2023-adhoc-reduction/reproduce.sh
```

The script uses a pinned upstream Perses commit by default. Override `PERSES_COMMIT` to perform a toolchain-drift retest.

## Paper vs reproduction

| Question | Paper | This reproduction |
|---|---|---|
| Can a grammar be added without editing Perses language integration code? | Yes, via AdhocCompiler + dynamic JAR loading | Scoped L2 directly exercises this path |
| Does dynamic loading preserve reduction effectiveness? | Same final token counts as native Perses on 5 C bugs | Only checks successful reduction of a new tiny language; no native-vs-adhoc equivalence claim |
| Runtime overhead | +2.6% mean in paper experiment | Not comparable at paper scale |
| Grammar build latency | ~2.5–15.7 s across six languages | Installer execution time is recorded as CI evidence, but runner/toolchain differences prevent direct comparison |
| Paper-scale reproduction | 5 real compiler bugs | Not attempted |

## Threats and limitations

- The live lane pins a modern Perses source revision, not the exact 2023 artifact revision. It is therefore also a **toolchain-drift probe**.
- `MiniCalc` is deliberately tiny. It validates the dynamic integration mechanism, not scalability or effectiveness on complex grammars.
- The oracle is synthetic and deterministic; it does not exercise a real compiler crash/miscompile.
- GitHub-hosted runner timing is noisy. Grammar-generation timing is evidence that the compiler ran, not a faithful reproduction of Table 4.
- A successful scoped L2 run says nothing about the paper's native-vs-adhoc equivalence across C benchmarks.

## Valuable extension

### L4: ad-hoc onboarding/toolchain drift matrix

Run the same language-extension corpus across paper-era Perses and current Perses, with several grammar sizes and Java/Bazel versions. Measure:

- grammar-JAR generation latency and output size;
- parser/reducer startup overhead;
- final token count and oracle calls versus a statically integrated/native language path where available;
- failures classified as grammar-normalization drift, Java compilation drift, dynamic-loading drift, or reducer drift.

This would test whether the paper's central usability claim survives several years of ANTLR/JDK/Bazel/Perses evolution, instead of only re-reporting the 2023 timing table.

## Promotion path

- **L1:** obtain/reprocess the paper's released five-subject outputs and recompute Tables 2–4.
- **L2:** already scoped to one fresh end-to-end dynamic-language run; strengthen it with a real non-native language/compiler bug.
- **L3:** rerun all five paper benchmark subjects with paper-era toolchain/artifact.
- **L4:** execute the cross-version/toolchain drift matrix above.

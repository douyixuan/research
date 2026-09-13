# Ad Hoc Syntax-Guided Program Reduction (ESEC/FSE 2023 Tool)

Paper: Jia Le Tian, Mengxiao Zhang, Zhenyang Xu, Yongqiang Tian, Yiwen Dong, Chengnian Sun, **Ad Hoc Syntax-Guided Program Reduction**, ESEC/FSE 2023 Tool Demonstrations, DOI `10.1145/3611643.3613101`.

Primary sources:

- Paper PDF: https://cs.uwaterloo.ca/~cnsun/public/publication/fse23-tool/fse23-tool.pdf
- Official Perses repository: https://github.com/uw-pluverse/perses
- Current installation guide: https://github.com/uw-pluverse/perses/blob/master/doc/install_new_languages.md
- Tool video: https://youtu.be/trYwOT0mXhU

## Core insight

Perses is algorithmically language-agnostic, but historically adding a grammar required converting it to Perses Normal Form, editing Perses integration/build code, and rebuilding Perses. `Perses^adhoc` moves that integration behind an `AdhocCompiler`: a user supplies an ANTLR grammar plus a small YAML language description, receives a dynamically loadable language JAR, and passes that JAR to the normal Perses reducer. The research claim is mainly an **engineering usability claim**: dynamic grammar support should preserve reduction effectiveness/efficiency while removing the need to edit the Perses codebase.

## Reproduction level

Current level: **L1 partial + scoped L2 live-minimal** once the official-current-source CI lane completes.

- **L0**: paper, official source, current documentation, build targets, and upstream adhoc system test are identified.
- **L1 partial**: recompute the arithmetic in Tables 1-4 from the numbers printed in the paper. This is not a rerun of the five historical compiler-bug reductions.
- **L2 scoped**: build a pinned current Perses commit, run its upstream adhoc system test, compile a fresh tiny `MiniExpr` grammar into a language JAR, and reduce a new input end-to-end through `--language-ext-jars`.
- **Not L3**: the five historical GCC/Clang cases are not rerun with the paper-era environment.
- **Not L4**: the proposed modern toolchain-drift experiment below is not yet executed at scale.

## L1: published-table recalculation

Run:

```bash
bash papers/2023-perses-adhoc/reproduce.sh
```

The checked-in `published_tables.json` transcribes Tables 1-4. `reproduce.py` only recomputes their aggregates; it does not create new experimental evidence.

| Quantity | Paper | Recalculated |
|---|---:|---:|
| Table 2 original-token mean | 29,764 | 29,764 |
| Table 2 Perses reduced-token mean | 155 | 154.8 -> 155 |
| Table 2 Perses-adhoc reduced-token mean | 155 | 154.8 -> 155 |
| Cases with equal native/adhoc final token count | 5/5 | 5/5 |
| Table 3 Perses mean time | 1,191 s | 1,191.4 s -> 1,191 |
| Table 3 adhoc mean time | 1,222 s | 1,221.6 s -> 1,222 |
| Table 3 Perses mean speed | 43.05 token/s | 43.048 token/s |
| Table 3 adhoc mean speed | 41.828 token/s | 41.828 token/s |
| Table 4 grammar-generation mean | "around 10 s" | 10.754 s |
| Table 4 slowest grammar | Java, ~16 s | Java, 15.672 s |

Two small reporting details are worth preserving rather than smoothing over:

1. Table 1's listed infrastructure LOC are `89 + 3 + 67 + 33 = 192`. The abstract/contribution text describes this as roughly **190 lines**, while Section 3.2 says the four files involve **200 lines**.
2. Directly averaging the five Table 3 rows gives a current arithmetic slowdown of **2.535%** (`1221.6 / 1191.4 - 1`). The paper reports **2.6%**, which is what one gets approximately from the displayed rounded means (`1222 / 1191 - 1 = 2.603%`). This is only rounding, not an experimental discrepancy.

## Scoped L2: fresh dynamic-language probe

`probe_official_adhoc.sh` pins Perses commit `6c6ae0db20fa83b0f85a71ca447f0c4d5e056bd2`, the same current-source pin used by the adjacent PPR reproduction. The CI lane performs four concrete steps:

1. build `perses_adhoc_installer_deploy.jar` and `perses_deploy.jar` from official source;
2. run the official `system_test_of_adhoc_fuzz_testing` target;
3. compile `case/MiniExpr.g4` + `language_kind.yaml` into `mini_expr.jar` without modifying Perses;
4. reduce a five-statement `.mini` input while preserving the property that identifier `target` remains.

The fixture is intentionally tiny. Success demonstrates the end-to-end mechanism claimed by the tool paper, not paper-scale effectiveness or efficiency.

Expected evidence is saved under `results/official/` and uploaded as the `perses-adhoc-official-l2` Actions artifact: build log, upstream system-test log, grammar-generation log, reduction log, original/reduced programs, environment metadata, and JSON summary.

## Paper vs reproduction

| Claim | Evidence here | Status |
|---|---|---|
| Dynamic grammar JAR can extend Perses without source edits | Fresh `MiniExpr` grammar compiled and loaded by official current source | scoped L2, CI pending at initial commit |
| Native Perses and adhoc mode have equal final token counts on 5 historical C bugs | Printed Table 2 arithmetic only | L1 partial; no historical rerun |
| Adhoc reduction is only ~2.6% slower on those 5 bugs | Printed Table 3 arithmetic only | L1 partial; no historical rerun |
| Grammar-library generation costs ~10 s on six paper grammars | Printed Table 4 arithmetic only | L1 partial; fresh tiny-grammar time is recorded separately and must not be compared as equivalent |
| New-language integration drops from ~190 LOC to ~20 LOC | Paper/source audit plus current one-command/JAR flow | L0/L2 mechanism evidence; human-effort claim not independently measured |

## Threats and limitations

- The L1 lane uses numbers printed in the paper, not raw historical logs.
- The original five GCC/Clang subjects, exact paper-era Perses revision, machine, JVM, Bazel, and compiler binaries are not reconstructed here, so no paper-scale timing claim is made.
- The L2 case is a purpose-built tiny grammar and property; it validates the dynamic-language path but cannot establish equality of effectiveness across complex real languages.
- Current Perses has evolved since 2023. A successful current-source run demonstrates durability of the mechanism, not equivalence to the 2023 implementation.
- GitHub-hosted build dependencies make the live lane network-dependent; build logs and the exact Perses commit are retained in the artifact.

## Most valuable extension (L4)

**Native-vs-adhoc differential reduction under modern Perses.** Select languages that Perses now supports natively, then also load the exact same grammars dynamically. For each language, generate or sample 50-100 property-preserving reduction tasks and compare:

- final token count and byte count;
- oracle invocations;
- wall-clock reduction time and grammar-JAR cold/warm build cost;
- parse/reduction failures;
- final-program equivalence under the property checker.

Run the matrix on both a paper-era revision and current Perses. Add ablations for `ORIG_FORMAT` vs compact formatting and current transformations such as Latra/T-Rec where applicable. This would directly test whether the 2023 "almost no side effect" result survives **toolchain drift**, rather than merely demonstrating that the feature still launches.

## Promotion path

To reach **L3**, recover the paper's five exact compiler-bug inputs and property scripts, pin the paper-era Perses/JDK/Bazel/compiler environment, run native and adhoc C reductions repeatedly, and report final token counts plus timing distributions. To reach **L4**, execute the modern differential matrix above with fixed hardware and multiple repetitions.

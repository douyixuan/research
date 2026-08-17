# Observed results — 2026-08-17

GitHub Actions run: https://github.com/douyixuan/research/actions/runs/31983355759

Workflow conclusion: **success**. Both the live bug-reproduction job and the pinned official-artifact structure audit passed.

## KT-74109

| Check | Observed result |
|---|---|
| Java equivalent hierarchy (`javac`, JDK 17.0.20) | **PASS** |
| Kotlin 2.1.0 | **REJECTED / historical bug reproduced** (exit 1) |
| Kotlin 2.4.10 | **REJECTED / bug still reproduces** (exit 1) |

Kotlin 2.1.0 diagnostic:

```text
error: class 'Child' must override 'func' because it inherits multiple implementations for it.
abstract class Child : Parent(), IChild
         ^^^^^^^^^^^
```

Kotlin 2.4.10 emits the same diagnostic.

## Interpretation

This provides fresh evidence for one CrossLangFuzzer finding: the equivalent Java inheritance graph is accepted, while both the paper-era Kotlin 2.1.0 compiler and the current stable 2.4.10 compiler reject the Kotlin subclass at the Java/Kotlin interoperability boundary.

The important extra result is **toolchain survival**: KT-74109 is still behaviorally reproducible on Kotlin 2.4.10. This conclusion is based on the compiler behavior, not on issue-tracker status.

The result remains **L2 scoped live-minimal**. We replayed a known minimized finding; we did not rediscover it through the generator/mutator search loop, and we did not rerun the paper's full 32-bug campaign.

The workflow artifact `crosslangfuzzer-kt74109-reproduction` contains the exact `javac`, Kotlin 2.1.0, and Kotlin 2.4.10 logs plus the generated summary.

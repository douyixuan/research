# Experiment design

## Hypotheses

H1. Repeated candidate generation causes redundant property-oracle executions when caching is disabled.

H2. STR/SHA/ZIP/RCC caches must not alter the final reduced program; caching is an execution optimization, not a semantic transformation.

H3. A refreshable interval representation can retain useful cache hits while using fewer key bytes than content-based keys when candidates are subsequences of the current best program.

## Workload

The fresh L2 probe generates one 32-fragment C program. Exactly three fragments contribute to the observed output; the rest are removable. A deterministic multi-pass chunk/single-element reducer repeatedly invokes a real `gcc -O0` compile-and-run oracle requiring stdout `3`.

This is designed to exercise the paper's cache invariant rather than to imitate its 31-bug distribution.

## Independent variables

Cache mode: `none`, `str`, `sha`, `zip`, `rcc`.

## Measurements

- final configuration;
- number of actual compile+execute oracle calls;
- cache hits;
- live cache entries at termination;
- peak encoded-key bytes (representation proxy only).

## Acceptance criteria

1. Every cache mode reaches the identical expected final configuration `[3, 11, 19]`.
2. At least one cache mode performs fewer real oracle calls than no-cache.
3. RCC-like peak key bytes are lower than SHA-512 key bytes.
4. The script exits non-zero if any invariant fails.

## Paper-scale design

A faithful L3 run should use the official Perses Docker setup, historical GCC/Clang property-test images, all 31 bug subjects, and the paper's cache modes and repetitions. Record raw runtime JSON and cache-memory logs before aggregation. Hardware, JVM flags, compiler versions, Perses commit, Docker image digests, CPU model, and repetition order should be pinned because memory/runtime are hardware-sensitive.

## Extension / ablation

Run a factorial experiment over reducer `{Perses, WDD, SFC, Latra, T-Rec, DRReduce}` × cache `{none, STR, SHA-512, ZIP, RCC, BLAKE3, bitmap}` × toolchain era `{paper-era, current}`. Use equal oracle-call budgets and at least 10 repeated runs for timing. Separate candidate-generation effects from cache-representation effects by replaying a fixed candidate trace through every cache implementation. This trace-replay baseline is important: otherwise a reducer that generates fewer duplicates can make a cache look worse even when the representation itself is superior.

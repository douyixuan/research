# On the Caching Schemes to Speed Up Program Reduction

Yongqiang Tian, Xueyan Zhang, Yiwen Dong, Zhenyang Xu, Mengxiao Zhang, Yu Jiang, Shing-Chi Cheung, Chengnian Sun. ACM TOSEM 33(1), 2023. DOI: 10.1145/3617172.

Paper: https://cs.uwaterloo.ca/~cnsun/public/publication/tosem23b/tosem23b.pdf  
Official implementation/reproduction guide: https://github.com/uw-pluverse/perses/blob/master/doc/RCC.md

## Reproduction level

**L0 artifact/toolchain audit + scoped L2 mechanism model.**

This is **not L1**: the paper's 31-subject raw measurements were not reprocessed here. It is **not L3**: the historical 31-bug experiment requires old GCC/Clang environments, long-running Docker jobs, and substantially more memory than ordinary hosted CI.

## Core insight

Program reducers often generate the same candidate program more than once. Caching can avoid repeated expensive property checks, but storing full program strings can itself consume substantial memory. The paper evaluates several cache representations and proposes **Refreshable Compact Caching (RCC)**:

1. encode a candidate losslessly as slicing intervals of the current minimum program; and
2. when the minimum shrinks, discard cached variants that are no longer subsequences of the new minimum and therefore cannot reappear later in deletion-based reduction.

The paper reports that caching avoids **61.8%** of property queries for HDD and **24.3%** for Perses. RCC is reported to reduce peak cache size versus the second-best scheme by **96.4%** for HDD and **91.74%** for Perses.

## What actually ran

### A. Deterministic scoped L2 mechanism model

`reproduce.py` executes a synthetic reduction trace with repeated adjacent fragments. It checks three RCC invariants:

- candidate interval encoding is lossless;
- duplicate variants collapse to one canonical cache key;
- after an accepted minimum shrink, stale cached variants that cannot be subsequences of the new minimum are removed.

Observed deterministic result:

- no cache: **25** synthetic property-oracle evaluations;
- RCC model: **3** evaluations;
- cache hits: **22**;
- synthetic oracle-call reduction: **88%**.

The 88% number is deliberately constructed by the tiny duplicate-heavy fixture and is **not comparable** to the paper's 24.3% Perses average.

Run the always-supported lane with:

```bash
bash papers/2023-rcc-cache/reproduce.sh
```

The result is written to `results/mechanism-summary.json` and uploaded by `paper-rcc-cache.yml`.

### B. Official Perses integration audit

A live implementation probe exposed material toolchain drift rather than producing a valid paper-style result:

- **Perses v2.7 (2026-08-26):** the no-cache tiny reducer case ran, but the public `--query-cache-type` selector used by the old RCC scripts is no longer present in the current CLI/source. The current reduction driver reports a fixed `CONTENT_SHA_HASH_FORMAT` cache type, while the still-present historical `benchmark/rcc-exp-script/` continues to reference `--query-cache-type COMPACT_QUERY_CACHE`.
- **Perses v1.9 (2025-01-10):** its published CLI still exposes `--query-cache-type COMPACT_QUERY_CACHE`, so a historical live scaffold is included. However, the prebuilt v1.9 JAR failed even on the default tiny case in the current GitHub-hosted runner, including a Java 21 attempt. Because that integration did not complete, no v1.9 result is claimed as L2.

The historical probe is therefore opt-in rather than a required CI lane:

```bash
RCC_HISTORICAL_LIVE=1 bash papers/2023-rcc-cache/reproduce.sh
```

The GitHub Action exposes the same probe through `workflow_dispatch` with `historical_live=true`. A successful future run may be labeled scoped L2; a failed run is evidence of environment/toolchain drift only.

## Experiment design

| Question | Measurement | Status |
|---|---|---|
| Is compact interval encoding lossless? | encode/decode synthetic subsequence | reproduced |
| Do duplicate candidates collapse to one cache key? | repeated identical variants | reproduced |
| Does refresh remove stale entries after the minimum shrinks? | cache before/after accepted shrink | reproduced |
| Does current Perses still expose paper RCC selection? | inspect/run v2.7 | no: selector drift found |
| Can an RCC-capable tagged release run in hosted CI? | v1.9 default/no-cache/RCC scaffold | currently blocked before valid comparison |
| Can paper Tables/RQs be recomputed? | released 31-subject raw outputs | not done; no L1 claim |

## Paper vs reproduction

| Item | Paper | This repository |
|---|---:|---|
| Subjects | 31 real GCC/Clang compiler bugs | synthetic deterministic trace; tiny integration probes |
| Reducers | HDD + Perses | RCC mechanism model; Perses integration audit |
| Cache policies | no cache, STR, ZIP, SHA, RCC + ablations | model: no-cache vs RCC; live historical scaffold: no-cache vs RCC |
| Queries avoided | HDD 61.8%; Perses 24.3% average | 88% synthetic model, intentionally non-comparable |
| Peak memory advantage | RCC 96.4% HDD; 91.74% Perses vs second-best | not measured |
| Actual level | paper-scale evaluation | L0 + scoped L2 mechanism |

## Blockers and requirements for higher levels

The current public Perses release can no longer select RCC through the paper's documented cache-type flag, and the available v1.9 binary did not complete the tiny hosted-runner integration. A faithful live reproduction therefore needs either a paper-era Perses build/commit or a compatible historical environment in which `COMPACT_QUERY_CACHE` can be executed and profiled.

The official RCC guide recommends Ubuntu 20.04, Docker, x86 hardware, and **128 GB RAM** for the full experiment; it also notes a roughly 20-minute Perses build inside the benchmark environment. Those requirements make the 31-subject experiment inappropriate for the default hosted Action.

## Threats and limitations

The mechanism fixture intentionally contains many duplicate candidates, so its query savings estimate is not externally valid. It models the two central RCC data-structure invariants but is not the Perses implementation. The current hosted GCC/JVM environment differs from the paper environment. Peak memory, cache-key allocation, refresh cost, and repeated-run variance are not measured. The failed historical integration has not been assigned a speculative root cause; it remains an explicit blocker.

## Most useful extension

**Toolchain-drift × cache-policy cost matrix.** Use a fixed set of post-paper GCC/LLVM bugs and compare a paper-era Perses build with a current build under no-cache / full-string / SHA / RCC policies, while holding reducer transformations and oracle budget constant. Record:

- unique and duplicate property queries;
- wall time and property-test time separately;
- peak cache bytes and bytes per retained key;
- refresh count and stale-key removal fraction;
- final reduced token count and any cache-safety disagreement;
- variance over repeated runs.

This would show whether RCC's memory/query advantage survives modern reduction pipelines or was coupled to the 2023 search order and benchmark distribution.

## Path to higher levels

**L1:** obtain the authors' released/raw 31-subject query/time/memory outputs and recompute the paper tables with the official aggregation scripts.  
**L2 official implementation:** execute `COMPACT_QUERY_CACHE` successfully on at least one fresh end-to-end reduction case and compare it with no-cache under the same reducer configuration.  
**L3:** run the historical benchmark environment across all 31 compiler bugs with repeated measurements and sufficient RAM.  
**L4:** execute the toolchain-drift/cache-policy matrix above with fixed budgets and statistical reporting.

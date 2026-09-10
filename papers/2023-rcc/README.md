# On the Caching Schemes to Speed Up Program Reduction (RCC)

Yongqiang Tian, Xueyan Zhang, Yiwen Dong, Zhenyang Xu, Mengxiao Zhang, Yu Jiang, Shing-Chi Cheung, Chengnian Sun. ACM TOSEM 33(1), published 2023.

Paper: https://doi.org/10.1145/3617172  
Official implementation/reproduction guide: https://github.com/uw-pluverse/perses/blob/master/doc/RCC.md

## Core insight

Program reducers repeatedly generate the same candidate program. Caching avoids rerunning an expensive property oracle, but storing whole candidate strings can consume too much memory. The paper evaluates STR, ZIP and SHA representations and proposes **Refreshable Compact Caching (RCC)**: encode a candidate by intervals relative to the current best program, then refresh the cache whenever a new best is found so entries that can never be revisited are discarded/re-encoded.

The paper reports duplicate-query rates of 61.8% for HDD and 24.3% for Perses. Across 31 real C compiler bugs, caching improves runtime by 22.8% and 18.2% respectively. RCC is reported to reduce memory further than SHA, by 96.4% for HDD and 91.74% for Perses.

## Reproduction level

**L0 official-artifact audit + scoped L2 fresh mechanism reproduction.**

This is **not L1**: we did not reprocess the paper's full raw result set. It is **not L3**: we did not rerun all 31 compiler bugs with paper-era GCC/Clang/Perses under the authors' Docker environment.

### L0 evidence

The official Perses repository contains the RCC implementation and experiment scripts. The implementation uses compact interval encodings for reducer configurations and `refreshAndUpdateBest` to decode old entries, change the base program, re-encode surviving entries, and drop configurations that are no longer subsequences of the new best.

The authors' reproduction guide requires Docker because individual bug oracles need specific GCC/Clang versions, recommends **128 GB RAM** for all experiments, and gives a roughly **20 minute** Perses build step. The current automation runtime has no Docker, so paper-scale execution is not feasible here.

## Scoped L2 experiment

`reproduce.py` builds a deterministic 32-fragment C program and performs real `gcc -O0` compile + execute property checks while a small multi-pass reducer removes irrelevant fragments. Three fragments are necessary for the output property. The same reduction is run with:

- no cache;
- STR: full rendered source as cache key;
- SHA: SHA-512 key;
- ZIP: zlib-compressed source key;
- RCC-like interval encoding relative to the current best, with refresh after every successful reduction.

Run:

```bash
./reproduce.sh
```

The local run on GCC 14.2.0 produced:

| Scheme | Oracle calls | Cache hits | Peak key-byte proxy | Final config |
|---|---:|---:|---:|---|
| none | 51 | 0 | 0 | `[3, 11, 19]` |
| STR | 37 | 14 | 12,822 | `[3, 11, 19]` |
| SHA-512 | 37 | 14 | 2,368 | `[3, 11, 19]` |
| ZIP | 37 | 14 | 5,121 | `[3, 11, 19]` |
| RCC-like | 37 | 14 | 16 | `[3, 11, 19]` |

Caching avoided **14/51 = 27.45%** of actual compile+execute oracle calls. The RCC-like cache's peak key-size proxy was **99.32% lower than SHA-512** in this tiny experiment. All schemes converged to the same minimal three-fragment result.

These percentages are **not paper-result reproductions**. The paper's memory measurements are JVM cache-memory measurements on real compiler-bug workloads; ours is only the sum of encoded key bytes in a synthetic deterministic probe. Its purpose is to validate the mechanism end-to-end and make the invariant executable in CI.

## Paper vs reproduction

| Question | Paper | This work |
|---|---|---|
| Do reducers revisit candidates? | Yes; 24.3% average duplicates for Perses | Yes; 14 cache hits avoid 27.45% of oracle calls in the scoped reducer |
| Does caching preserve reduction output? | Yes | Yes; all five modes reach `[3, 11, 19]` |
| Can compact refreshable encoding reduce cache footprint? | RCC beats STR/ZIP/SHA on real workloads | RCC-like key proxy peaks at 16 B vs 2,368 B for SHA; mechanism-only evidence |
| Paper-scale runtime/memory claims reproduced? | 31 real compiler bugs | **No** |

## Threats and limitations

The reduction workload is synthetic and intentionally creates repeated candidates; duplicate rate therefore cannot be compared directly with Perses/HDD. The RCC implementation here is a small independent model of interval encoding + refresh, not Perses' production Kotlin implementation or its exact compressor. `peak_key_bytes` excludes Python object overhead and is not comparable to JVM heap measurements. Only GCC 14 is used, whereas the paper requires multiple historical compiler versions and real bug-triggering programs.

## Promotion path

To reach **L1**, obtain or reconstruct the complete paper result artifacts and rerun the official analysis scripts for the reported runtime/query/memory tables. To reach **L3**, use an x86 Docker runner with approximately 128 GB RAM, pin the paper-era Perses/artifact revision and compiler images, run all 31 compiler-bug subjects for STR/SHA/ZIP/RCC/no-cache with the paper's repetitions and profiling settings, then archive raw JSON/logs as CI artifacts.

## Most useful extension

**Cache representation × reducer/toolchain drift under an equal oracle budget.** Re-run STR, SHA, ZIP and RCC on current Perses plus WDD/SFC/Latra/T-Rec/DRReduce, using both paper-era and current compiler bugs. Measure cache hit rate, peak memory, wall time, oracle calls, and `tokens removed / oracle call`. Add BLAKE3/content-addressed and compact bitmap/Roaring-style representations. This would show whether RCC's advantage survives modern reducers whose candidate-generation distributions differ substantially from 2023 Perses.

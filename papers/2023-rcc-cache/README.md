# On the Caching Schemes to Speed Up Program Reduction

Yongqiang Tian, Xueyan Zhang, Yiwen Dong, Zhenyang Xu, Mengxiao Zhang, Yu Jiang, Shing-Chi Cheung, Chengnian Sun. ACM TOSEM 33(1), 2023. DOI: 10.1145/3617172.

Paper: https://cs.uwaterloo.ca/~cnsun/public/publication/tosem23b/tosem23b.pdf  
Official reproduction guide / implementation: https://github.com/uw-pluverse/perses/blob/master/doc/RCC.md

## Reproduction level

**L0 artifact/claim audit + scoped L2 current-release mechanism probe.**

This is **not L1**: the paper's 31-subject raw measurements are not committed here and this run does not recompute the paper tables from released raw outputs. It is **not L3**: the full benchmark needs historical GCC/Clang Docker images, many hours, and the authors recommend 128 GB RAM.

## Core insight

Program reducers often generate the same candidate program more than once, so property checks are wasted unless variants are cached. Straight string caching (STR) can itself become a memory bottleneck. The paper evaluates ZIP and SHA compression and proposes **Refreshable Compact Caching (RCC)**:

1. encode a candidate losslessly as slicing intervals of the current minimum program; and
2. when the minimum shrinks, remove cached variants that cannot be subsequences of the new minimum and therefore cannot recur.

The paper reports that caching avoids 61.8% of property queries in HDD and 24.3% in Perses. RCC is reported to reduce peak cache size versus the second-best scheme by 96.4% in HDD and 91.74% in Perses, while preserving the same query count as the other correct caching schemes.

## What is actually run here

`reproduce.sh` performs two independent checks.

### A. Deterministic RCC mechanism trace

`reproduce.py` runs a synthetic reduction trace with adjacent identical fragments. It checks that:

- identical candidate variants map to one canonical interval key;
- interval encoding is lossless;
- a minimum shrink invalidates stale cache entries that are not subsequences of the new minimum;
- cached execution avoids redundant oracle calls without changing the accepted minimum.

This is a mechanism-level **scoped L2**, not the official Perses implementation.

### B. Live current Perses probe

The script downloads the official **Perses v2.7** release JAR and verifies SHA-256 `1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427`. It then runs the same tiny C reducer workload twice:

- no query cache: `--query-caching FALSE`
- RCC: `--query-caching TRUE --query-cache-type COMPACT_QUERY_CACHE`

Vulcan, Latra, SFC, LPR, and T-Rec are disabled and `--threads 1` is used so the comparison isolates the query-cache path as far as practical. The property checker requires all twelve repeated `+=` fragments, then compiles and executes the candidate with GCC. The external oracle invocation count is recorded directly.

Run:

```bash
bash papers/2023-rcc-cache/reproduce.sh
```

Generated evidence is written to `results/` and uploaded by `paper-rcc-cache.yml`.

## Experiment design

| Question | Measurement | Pass condition |
|---|---|---|
| Does canonical compact encoding preserve a variant? | encode/decode synthetic subsequence | exact token equality |
| Does refresh remove stale entries? | cache entries before/after accepted minimum shrink | at least one stale entry removed |
| Does caching suppress duplicate checks in the mechanism trace? | external synthetic oracle calls | cached calls < no-cache calls |
| Does current Perses still expose the paper's RCC implementation? | v2.7 live run with `COMPACT_QUERY_CACHE` | reducer completes and final candidate passes oracle |
| Does RCC add property checks on the tiny live case? | external test-script invocations | RCC calls <= no-cache calls |

## Paper vs reproduction

| Item | Paper | This reproduction |
|---|---:|---|
| Subjects | 31 real GCC/Clang compiler bugs | 1 synthetic C workload + deterministic mechanism trace |
| Reducers | HDD and Perses | Perses v2.7 + mechanism model |
| Cache schemes | STR, ZIP, SHA, RCC (+ ablations) | no-cache vs RCC; mechanism-level canonical encoding/refresh |
| Avoided queries | HDD 61.8%; Perses 24.3% average | see `results/live-perses-summary.json`; **not directly comparable** |
| Peak RCC advantage | 96.4% HDD; 91.74% Perses vs second-best | not measured |
| Level | paper-scale evaluation | L0 + scoped L2 |

## Artifact/toolchain audit

The official Perses repository still contains `doc/RCC.md`, the `benchmark/rcc-exp-script/` experiment driver, and current cache selections including `COMPACT_QUERY_CACHE`, `CONTENT_SHA_HASH`, `CONTENT_ZIP`, and `ORIG_CONTENT_STRING_BASED`. The 2026 v2.7 CLI also includes additional reducers and changed defaults, so a modern run is not a paper-era baseline unless those paths are controlled explicitly.

The official reproduction guide recommends Ubuntu 20.04, Docker, x86 hardware, and 128 GB RAM for the full experiment; it also notes that building Perses in the benchmark Docker takes about 20 minutes. The full paper-scale run is therefore intentionally not placed in ordinary CI.

## Threats and limitations

The live workload is synthetic and tiny, so its duplicate rate is intentionally constructed and cannot estimate the paper's 24.3% Perses average. Current Perses v2.7 is several years newer than the paper implementation, and cache internals/default reducer composition may have drifted. GCC on `ubuntu-latest` is also not the historical compiler environment used by the 31 benchmark subjects. External test-script counts measure property-oracle executions, not Java object memory or cache-key memory.

## Most useful extension

**Toolchain-drift × cache-policy cost matrix.** Re-run a small fixed set of post-paper GCC/LLVM bugs with paper-era Perses and v2.7 under no-cache / STR / SHA / RCC, holding reducer transformations and oracle budget constant. Record:

- unique vs duplicate property queries;
- wall time and property-test time separately;
- peak cache bytes and bytes per retained key;
- cache refresh events and stale-key removal fraction;
- final reduced token count to catch any semantic/cache-safety regression.

This would distinguish whether RCC's advantage is stable under modern reducer pipelines or was partly coupled to the 2023 search order and benchmark distribution.

## Path to higher levels

**L1:** obtain/release the authors' raw 31-subject time/query/memory outputs and re-run the official CSV aggregation scripts, checking Tables 3–6.  
**L3:** use the historical benchmark Docker/toolchains and paper-era Perses/HDD configuration on all 31 subjects with repeated runs and enough RAM.  
**L4:** execute the toolchain-drift matrix above, ideally adding a fixed-memory-budget baseline and reporting variance across repeated runs.

# Vulcan — Pushing the Limit of 1-Minimality of Language-Agnostic Program Reduction

Xu, Tian, Zhang, Zhao, Jiang, Sun. OOPSLA 2023. DOI: 10.1145/3586049.

- Paper/publication page: https://research.monash.edu/en/publications/pushing-the-limit-of-1-minimality-of-language-agnostic-program-re/
- Official artifact: https://zenodo.org/records/8197652
- Upstream implementation: https://github.com/uw-pluverse/perses

## Core insight

A deletion-based reducer can reach a **1-minimal** program even though the program is still much larger than necessary. Vulcan deliberately permits property-preserving edits that do **not** immediately shrink the program. Those edits can move the candidate out of the deletion reducer's local minimum, after which ordinary deletion can make progress again.

The public Perses implementation contains Vulcan-specific reducers including identifier replacement, subtree replacement, and local exhaustive pattern reduction. The identifier-replacement implementation explicitly tries replacing identifier uses so that a now-unused definition may become deletable.

## Reproduction level

**Current level: L0 official-artifact / implementation audit + scoped L2 mechanism reproduction + current-Perses drift probe.**

This is **not L1**: the paper's released result tables have not been reprocessed here. It is **not L3**: the paper-scale C/Rust/SMT experiments have not been rerun. The deterministic L2 case is a fresh, small compile-and-execute experiment designed only to test the central local-minimum-escape mechanism.

## Paper claims used as reference

The paper reports that Vulcan's final results contain, on average, **33.55% fewer tokens for C, 21.61% fewer for Rust, and 31.34% fewer for SMT-LIBv2** than Perses. It also reports a **10.07%** further reduction over C-Reduce on the evaluated C cases.

These numbers are reference claims, not reproduced results in this directory.

## Experiment design

`case/small.c` deliberately creates a deletion-local minimum:

```c
int x = 42;
int y = x;
printf("%d\n", y);
```

At statement granularity, deleting either declaration breaks compilation and deleting the `printf` breaks the output oracle. The deletion-only baseline is therefore 1-minimal. A Vulcan-style non-deletion edit can replace the use of `y` in `printf` with `x`; that edit preserves the property without initially reducing size, but it makes the `y` declaration deletable on the next pass.

`reproduce.py` executes that mechanism with a real C compiler and compile/run oracle. `probe_current_perses.sh` separately downloads the SHA-256-pinned Perses v2.7 release and runs the same fixture with Vulcan disabled and enabled, while disabling Latra/SFC/LPR/T-Rec so newer auxiliary reducers do not contaminate the comparison.

Run:

```bash
./papers/2023-vulcan/reproduce.sh
```

Outputs are written to `papers/2023-vulcan/results/` and uploaded by CI.

## Paper vs reproduction

| Question | Paper | This reproduction |
|---|---|---|
| Can an AGR 1-minimum still contain removable material? | Yes, across multilingual benchmark suites | Yes, on one fresh C fixture at statement granularity |
| Can a non-deletion transformation unlock more deletion? | Yes | Yes; identifier replacement is followed by an additional deletion |
| C improvement vs Perses | 33.55% average fewer tokens | Not comparable; tiny synthetic fixture only |
| Rust improvement vs Perses | 21.61% average fewer tokens | Not run |
| SMT-LIBv2 improvement vs Perses | 31.34% average fewer tokens | Not run |
| Further reduction vs C-Reduce | 10.07% average | Not run |
| Paper-era implementation | Official Vulcan artifact | Audited, but not executed at paper scale |
| Modern implementation drift | N/A | Perses v2.7 off/on probe, pinned by checksum |

## Official artifact audit / blockers

The Zenodo artifact is **385.4 MB** and contains source, benchmarks, scripts, and documentation. Its documented C/Rust setup pulls a Docker environment that takes **nearly 100 GB**. The documented single-CPU runtimes are roughly 1 hour even for the C RQ1 demo and about 94 hours for the full RQ1 C experiment; other full C experiments are similarly multi-day. The artifact also states that Perses was updated after the paper evaluation and that refactoring can cause small deviations from paper numbers.

For those reasons the hosted CI lane does not claim paper-scale execution. To advance to **L1**, unpack the official artifact and recompute the published tables from released outputs if available. To advance to **L3**, run the official C/Rust/SMT scripts in the documented Docker environments with sufficient disk and CPU time and preserve raw JSON/CSV outputs.

## Threats and limitations

The L2 fixture uses statement-level deletion rather than Perses' full grammar/tree search, so its 1-minimality is scoped to that candidate space. It contains one C program and one output property, so it does not establish the paper's magnitude of benefit or language generality. The Perses v2.7 probe is a **toolchain-drift check**, not the 2023 artifact; modern Perses contains several later reducers and pipeline changes, which is why they are explicitly disabled where possible. Compiler version, parser behavior, reduction ordering, and caching can all alter oracle counts and final size.

## Most valuable extension

Run a **paper-era vs current-Perses transformation-ROI matrix** on post-paper compiler bugs. Keep the same property checker and oracle-call budget, then compare deletion-only, each Vulcan auxiliary reducer separately, full Vulcan, WDD/SFC/Latra, and current default Perses. Record final tokens, accepted transformations, oracle calls, wall time, and failures by category. This would separate three effects that later papers often conflate: better search ordering, genuinely useful non-deletion transformations, and toolchain/benchmark drift.

A particularly useful ablation is **leave-one-transformation-family-out**. If most modern benefit comes from a small subset of replacement patterns, that is evidence for adaptive transformation scheduling rather than an ever-growing fixed reducer pipeline.

## CI

`.github/workflows/paper-vulcan.yml` runs the deterministic L2 mechanism and the pinned current-Perses probe, then uploads source reductions, summaries, and logs as the `vulcan-reproduction` artifact.

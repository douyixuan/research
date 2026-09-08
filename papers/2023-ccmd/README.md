# Compilation Consistency Modulo Debug Information (CCMD / Dfusor)

Theodore Luo Wang, Yongqiang Tian, Yiwen Dong, Zhenyang Xu, Chengnian Sun — ASPLOS 2023.

Paper: https://doi.org/10.1145/3575693.3575740  
Official artifact: https://doi.org/10.5281/zenodo.7217505

## Core insight

CCMD states that enabling debug information must not change the generated machine code. Dfusor stresses this property by mutating compilable C seeds with three transformation families: **RCL** (randomized code lowering), **OCP** (code-position obfuscation with `#line`/whitespace changes), and **FCO** (fine-grained optimization control via compiler attributes). The paper reports 23 GCC/Clang CCMD bugs; for 100 sampled variants, Dfusor produced 214% more DWARF DIEs and 36% more distinct DIE types than the seeds.

## Reproduction level

**Current level: L0 artifact audit + scoped L2 live-minimal. This is not L1 or L3.**

- **L0:** verified the paper's artifact appendix and archived Zenodo DOI. The official artifact is a Docker image (`ASPLOS23-dfusor.tar`) and the paper estimates about 15 GB of disk. The appendix describes transformation generation, not a released table of all evaluation outputs, so no L1 claim is made here.
- **Scoped L2:** independently exercise the CCMD oracle on fresh deterministic C fixtures representing the three transformation ideas. Each fixture is compiled by available GCC and Clang with and without `-g3`, at `-O0` and `-O2`. The executable `.text` bytes and runtime output must be identical between debug/non-debug builds.
- **Debug-complexity probe:** count DWARF DIEs, approximate distinct DIE types as `(DW_TAG, set(DW_AT_*))`, and sum `.debug*` section bytes for each debug build; compare transformed fixtures with the seed.
- **Not L1:** author-released paper-scale result tables are not reprocessed.
- **Not L3:** the official randomized Dfusor/Csmith campaign and historical compiler versions are not rerun.

## One-command run

```bash
bash papers/2023-ccmd/reproduce.sh
```

Requires Python 3, GCC and/or Clang, GNU `objcopy`, and GNU `readelf`. Results are written to `papers/2023-ccmd/results/summary.json`.

## Experiment design

The deterministic fixtures isolate Dfusor's ideas without claiming source equivalence to the official implementation:

| Fixture | Mechanism |
|---|---|
| `seed` | compact baseline program |
| `rcl` | lower compound expressions into temporaries and control flow into labels/gotos |
| `ocp` | insert `#line` directives that change synthetic file/line locations |
| `fco` | add function/variable attributes such as `noinline`, `hot`, and `aligned` |
| `combined` | combine RCL + OCP + FCO |

For every compiler/optimization/fixture pair the script performs two builds using identical flags except for `-g3`. It extracts only the executable `.text` section before hashing, avoiding the expected differences in debug sections. Runtime stdout is also compared. Finally, all transformed fixtures must preserve the seed's observable stdout.

A local validation run on GCC 14.2 and Clang 17 produced **20/20 CCMD-passing pairs** and semantic-equivalence checks passed. The combined fixture increased DIE count relative to the seed by roughly **1.36–1.43× on GCC** and **1.69–1.88× on Clang** in that environment. These are tiny modern-toolchain observations, not reproductions of the paper's 3.46× aggregate.

## Paper vs reproduction

| Item | Paper | This reproduction |
|---|---|---|
| Test scale | continuous campaign, 100 variants sampled for debug-info study | 5 deterministic fixtures × 2 compilers × 2 optimization levels |
| CCMD bugs | 23 total: 9 GCC, 14 Clang | no new bug observed in local validation |
| Debug-info quantity | RCL 2.92× DIEs; RCL+FCO(+OCP) 3.46× on average | combined fixture increases DIEs, but much less than paper-scale random variants |
| Distinct DIE types | RCL 1.21×; RCL+FCO(+OCP) 1.36× | modest increase; compiler/version dependent |
| Compiler coverage | up to 6.00% Clang branch and 6.82% GCC branch improvement | not measured |
| Official artifact | Dfusor Docker image, x86, ~15 GB | not downloaded/run in hosted CI |

The discrepancy in debug amplification is expected: the L2 fixtures are small and deterministic, while the paper repeatedly mutates generated programs and samples substantially larger variants.

## Threats and limitations

- The fixtures are paper-inspired mechanism probes, not output from the authors' Dfusor binary.
- `.text` equality is a strong executable-code check on this ELF/x86 CI path, but does not compare every machine-code-bearing section, relocations, or LTO objects.
- Modern GCC/Clang have fixed many historical CCMD bugs; passing today does not invalidate the paper's findings.
- DIE parsing uses GNU `readelf`; distinct-type counting approximates the paper's definition from emitted tags and attribute keys.
- `-O0`/`-O2` cover only part of the paper's flag space (`-O0..-O3`, `-Os`, `-g1..-g3`, LTO/thin-LTO).
- The official artifact's random transformations and Csmith/tkfuzz/Hermes seeds require a much heavier environment and are intentionally excluded from normal GitHub-hosted CI.

## Path to L3

Provision an x86 self-hosted runner with Docker and at least 30 GB free disk (the paper estimates ~15 GB for the artifact alone), stage `ASPLOS23-dfusor.tar`, load it, and follow the artifact README to generate Csmith seeds and Dfusor variants. Pin paper-era GCC/Clang revisions, run the complete flag matrix and repeated random trials, then archive every seed/variant, command, `.text` comparison, DWARF statistics, compiler revision, and failure reproducer.

## Most valuable extension (L4)

**CCMD drift matrix on modern LLVM/GCC.** Run the same post-paper corpus across compiler revisions and debug formats (`-g1/-g2/-g3`, DWARF4/5, LTO/thin-LTO), classify every mismatch by optimization pass and machine-code section, and compare Dfusor's RCL/OCP/FCO against a coverage-guided or learned transformer under the same compile-time budget. This directly tests whether debug-info-induced optimizer divergence has migrated to new passes as toolchains evolved.

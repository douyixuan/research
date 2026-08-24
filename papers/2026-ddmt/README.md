# DDMT: Delta Debugging in the Absence of Test Oracles Through Metamorphic Testing

- Authors: Mingyue Jiang, Yongqiang Tian, Tsong Yueh Chen
- Public version: arXiv:2607.00929 v1, 2026-07-01
- Status: under review (authors' version)
- Official artifact: `ymxl85/DDMT`
- Artifact snapshot pinned here: `43c2f12306f02582779b24766dbddeadce9480e3`
- Current reproduction level: **scoped L1 + scoped L2 mechanism**

## Core insight

Classic delta debugging needs a `test(candidate) -> PASS/FAIL` oracle. DDMT replaces that oracle-dependent predicate with a metamorphic predicate:

```text
candidate source input
    |
    +-- MR --> follow-up input
    |              |
    v              v
  program        program
    |              |
    +---- compare outputs under MR ----+
                       |
                 violation / satisfaction
```

A metamorphic-relation (MR) violation becomes the property that delta debugging preserves. This is important because the source input itself does not need a known expected output, and may not even be failing when judged in isolation.

## Paper claims used as reproduction targets

The paper evaluates 66 faulty programs: 58 Siemens variants plus 8 GCC/Clang compiler cases. For Siemens, it compares ordinary `ddmin` with DDMT using different MRs. With the best MR, Table VI reports:

| Subject | ddmin size | DDMT size | ddmin queries | DDMT queries | ddmin time (s) | DDMT time (s) |
|---|---:|---:|---:|---:|---:|---:|
| printtokens | 3.72 | 2.43 | 30 | 19 | 0.08 | 1.68 |
| printtokens2 | 1.96 | 2.24 | 21 | 22 | 0.06 | 1.97 |
| replace | 3.28 | 2.89 | 19 | 17 | 0.13 | 0.19 |
| schedule | 14.70 | 9.30 | 221 | 162 | 1.36 | 13.94 |

The compiler experiment reports an average of 369 vs 368 tokens and 4666 vs 4623 queries for Perses vs Perses-DDMT.

## What is reproduced here

### L1 — released-result reprocessing (scoped)

`recompute_siemens.py` reparses the official released Siemens result summaries and joins `ddmin` and DDMT records by `(faulty version, test case)` before computing means. It validates the paper's Table VI values for every best-MR row that is actually represented in the public artifact.

The artifact audit is deliberately part of the result: the paper identifies **MR3 as the best MR for `replace`**, but the released `benchmarks/Siemens/` directory contains `replace-MR1`, `replace-MR2`, and `replace-dd` summaries, with no `replace-MR3` summary. Therefore this repository calls the result **scoped L1**, not full L1.

### L2 — fresh mechanism-level end-to-end run (scoped)

`mechanism_smoke.py` runs a fresh Python 3 implementation of `ddmin` with an MR-based predicate. The toy target is a tokenizer whose output should be invariant to adding a trailing comment. A seeded bug makes that relation fail only when the source contains a trigger token. DDMT reduces an oversized source to the minimal source that still causes the relation violation **without consulting a correct implementation or expected output**.

This validates the algorithmic mechanism, not the paper's Siemens/Perses implementation. The upstream `ddmin-DDMT` code is Python 2-era code with hard-coded local paths and external Java/Siemens binaries, so calling this paper-scale L2/L3 would be inaccurate.

## Paper vs reproduction

| Question | Paper | This reproduction |
|---|---|---|
| Can reduction work without an explicit expected-output oracle? | Yes, via MR violations | Yes, fresh mechanism-level run |
| Are released Siemens results machine-reprocessable? | Replication package claimed | Yes for released rows; `replace` best-MR data is missing |
| Does a good MR improve size/query count? | Often; up to 12–37% smaller and 11–37% fewer queries on some Siemens subjects | L1 checks released best-MR summaries where available; L2 demonstrates the mechanism only |
| Compiler-scale oracle-deficient reduction | 8 GCC/Clang subjects with Perses-DDMT | Not rerun; requires old compiler/Perses environment and benchmark-specific setup |

## Reproduction command

```bash
bash papers/2026-ddmt/reproduce.sh
```

Generated evidence is written to `papers/2026-ddmt/results/` and uploaded by GitHub Actions.

## Threats and limitations

1. The paper uses Ubuntu 16.04 and a Python 2-era ddmin implementation; modern hosted runners cannot execute it faithfully without environment reconstruction.
2. `replace`'s best-MR (MR3) summary is absent from the current artifact, so Table VI cannot be fully regenerated from released summaries.
3. The L2 test is a mechanism reproduction, not one of the 66 paper subjects.
4. MR quality is a confounder: DDMT can be materially better or worse depending on which relation is chosen.
5. `mrtest` usually executes the program twice plus follow-up generation/checking, so fewer queries do not automatically mean lower wall-clock cost.

## Best next experiment: MR portfolio selection

The strongest extension is not simply “add more MRs”, but make MR selection a measured optimization problem. For each reduction state, score candidate MRs by:

```text
expected reduction gain / (source run + follow-up run + MR construction/check cost)
```

Compare fixed-best-MR, random MR, round-robin portfolio, and an adaptive bandit policy on the same subjects. Report final size, total target executions, wall time, and MR-violation yield. This directly attacks the paper's main limitation—high sensitivity to MR quality—while accounting for DDMT's extra execution cost.

For compiler work, a practical variant is to use compiler metamorphic relations such as semantics-preserving source transformations or optimization-level relations, then compare `Perses/llvm-reduce + explicit oracle` against `reducer + MR predicate` on silent miscompilations.

## Upgrade path

- **Full L1:** obtain/release the missing `replace-MR3` result summary and reprocess all Table VI/VII rows.
- **Paper-subject L2:** containerize the upstream Python 2/Java/Siemens environment and rerun one published `printtokens` case.
- **L3:** reconstruct Ubuntu 16.04 + Perses + historical GCC/Clang subjects and rerun all 66 programs.
- **L4:** implement and evaluate adaptive MR selection / compiler-specific MR portfolios.

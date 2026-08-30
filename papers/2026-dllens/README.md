# DLLens — Enhancing Differential Testing with LLMs for Testing Deep Learning Libraries

**Venue:** ACM TOSEM 35(4), Article 88, 2026  
**DOI:** 10.1145/3735637  
**Authors:** Meiziniu Li, Dongze Li, Jianmeng Liu, Jialun Cao, Yongqiang Tian, Shing-Chi Cheung  
**Official artifact:** https://github.com/maybeLee/DLLens  
**Pinned artifact commit:** `0f617e92c34d60bfdd3bc06d80c17d938879ed9c`

## Reproduction level

**L1 partial + L0 implementation audit.**

This reproduction reprocesses released raw RQ1 round files and RQ4 confirmed-bug CSVs. It does **not** claim L2/L3: fresh counterpart synthesis requires a live LLM/API configuration plus the paper-era TensorFlow/PyTorch environment and can be expensive; the public artifact also states that it currently contains experiment results plus selected important code while code cleaning continues.

## Core idea

DLLens turns cross-library API equivalence into a differential-testing oracle. An LLM proposes a counterpart for an API in another DL library; validation filters hallucinated counterparts. DLLens then extracts path constraints, using LLM knowledge where static analysis cannot resolve upstream/native-library semantics, and uses those constraints to generate diverse inputs.

The TOSEM version reports three headline improvements over prior techniques:

- **1.84×** as many APIs with synthesized counterparts as the compared state-of-the-art techniques;
- **7.23%** more branch coverage under the same time budget on 200 sampled APIs;
- **1.88×** as many bugs on those 200 APIs.

Across the broader campaign it reports **71 detected bugs**, **59 confirmed**, including **46 previously unknown** and **13 known** bugs; **10** of the newly found bugs were fixed.

## What we actually recompute

`reproduce.py` reads the pinned artifact rather than notebook output cells.

### RQ1 — counterpart synthesis

Five raw round files per library are counted:

| Library | Per-round raw counts | Total | TensorScope baseline | Improvement |
|---|---:|---:|---:|---:|
| TensorFlow | 604, 37, 17, 14, 17 | **689** | 304 | **126.64%** |
| PyTorch | 608, 47, 34, 12, 11 | **712** | 458 | **55.46%** |
| Combined | — | **1401** | **762** | **1.84×** |

The per-round totals come directly from `data/working_dir/rq1/dllens/{tensorflow,pytorch}/round{1..5}.txt`. The TensorScope comparison values are the values used by the released RQ1 notebook; the artifact contains its reproduced TensorScope mapping files under `data/working_dir/rq1/tensorscope/`.

### RQ4 — confirmed bugs

The two released CSVs are re-aggregated using their `Bug Count` column rather than counting rows (some rows describe multiple bugs):

- TensorFlow confirmed bugs: **37**
- PyTorch confirmed bugs: **22**
- confirmed total: **59**
- previously unknown total, including those later fixed: **46**
- known total: **13**
- previously unknown and now fixed: **10**

The released confirmed-bug tables cannot by themselves rederive the paper's **71 detected** total because they intentionally list confirmed bugs; therefore this reproduction does not pretend that RQ4 is fully reproduced.

## Paper vs reproduction

| Claim | Paper | This run | Status |
|---|---:|---:|---|
| TF counterparts | 689 | 689 | ✅ raw-data L1 |
| PyTorch counterparts | 712 | 712 | ✅ raw-data L1 |
| Combined counterpart ratio | 1.84× | 1.84× | ✅ scoped L1 |
| Confirmed bugs | 59 | 59 | ✅ raw-data L1 |
| Previously unknown confirmed | 46 | 46 | ✅ raw-data L1 |
| Known confirmed | 13 | 13 | ✅ raw-data L1 |
| Newly found bugs fixed | 10 | 10 | ✅ raw-data L1 |
| All detected bugs | 71 | not independently reconstructed | ⚠️ partial |
| +7.23% branch coverage | +7.23% | not rerun today | ⚠️ not in this lane |
| 1.88× bugs on 200 APIs | 1.88× | not rerun today | ⚠️ not in this lane |

## Reproducibility drift

The work has a useful snapshot-drift story. The original 2024 arXiv version was titled **“DLLens: Testing Deep Learning Libraries via LLM-aided Synthesis”** and reported 56 bugs. The final TOSEM article reports 71 bugs and updated comparative results. Reproductions therefore must pin the camera-ready artifact/result snapshot rather than mix old arXiv claims with the final journal tables.

There is also publication-year drift: some author-facing listings historically grouped the work under 2025, while DBLP indexes the final article as TOSEM 35(4), 2026.

## Why L2/L3 is not claimed

A faithful fresh run must reconstruct the model/API and old DL stack, then execute:

```bash
python -u -m scripts.synthesize_counterpart
python scripts/extract_constraint.py
python scripts/gen_tests.py
```

That introduces model drift, API cost, nondeterminism, and TensorFlow/PyTorch version drift. Running a current model and calling it a reproduction would confound the technique with a different model distribution. A proper L2 should pin/model-log: model identity, decoding parameters, prompts, library versions, seed, token cost, accepted/rejected counterpart traces, and validation results.

## Threats and limitations

1. **Released-result dependence:** L1 recomputes released outputs; it does not prove the generation process produced them.
2. **Manual bug triage:** false-positive filtering and “known/new” classification contain human judgment and mutable GitHub issue state.
3. **Model drift:** the synthesis/constraint components depend on an LLM, so a 2026 rerun is not directly comparable without controlling model/version.
4. **Framework drift:** TensorFlow/PyTorch APIs, native kernels, and bugs evolve; current behavior can erase or create differential failures.
5. **Baseline fairness:** model budget, wall clock, API selection, and validity filtering must be normalized when comparing LLM and non-LLM baselines.

## Most valuable extension: post-cutoff, budget-normalized DLLens

Build a new benchmark from TensorFlow/PyTorch APIs and bugs introduced **after the evaluated model's training cutoff**, then compare:

- released DLLens configuration;
- a current small/cheap model;
- a current strong model;
- non-LLM baselines;

under equal **wall-clock + token/API-cost budgets**. Report counterpart validity, new branch edges, bugs found, false-positive rate, cost per accepted counterpart, and cost per unique bug. This separates the value of the DLLens harness/validation loop from model memorization and raw model scaling.

A second useful ablation is to replay the exact same proposed counterparts through paper-era vs current TensorFlow/PyTorch to quantify **framework/toolchain drift independently of model drift**.

## Run

```bash
./papers/2026-dllens/reproduce.sh
```

The script clones the official artifact at the pinned commit and writes `papers/2026-dllens/results/dllens-report.json` plus a Markdown summary. Set `DLLENS_ARTIFACT=/path/to/DLLens` to reuse an existing checkout.
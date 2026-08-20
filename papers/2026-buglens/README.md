# BugLens — bisection-based compiler bug deduplication

Paper: **On the Feasibility of Deduplicating Compiler Bugs with Bisection** (ISSTA 2026)

- Authors: Xintong Zhou, Zhenyang Xu, Yongqiang Tian, Chengnian Sun
- Current arXiv v3: https://arxiv.org/abs/2506.23281 (revised 2026-07-03)
- Author publication list: https://yqtian.com/pub.html
- Reproduction artifact used here: https://github.com/buglens-artifact/BugLens
- Artifact pin: `db94d68400e25197c5a93e5f420cf35ec4ae698c`

## TL;DR

The paper reframes compiler bug deduplication around a very cheap signal: the **failure-inducing commit (FIC)** found by version-control bisection. Test programs whose failures begin at different commits are almost certainly distinct bugs. Because one commit can introduce multiple bugs, BugLens adds the **bug-triggering optimization** as a secondary discriminator.

The attractive systems idea is not a new similarity model; it is changing the representation of a bug from “properties of the triggering program/execution” to “where in compiler history the failure starts.” That removes much of the language-specific feature engineering used by Tamer/D3 and reduces reliance on test-case minimization.

## Paper claims / research questions

1. **RQ1 — bisection-only effectiveness:** how useful is FIC alone as the deduplication key?
2. **RQ2 — false-negative mitigation:** can bug-triggering optimizations split distinct bugs that share the same FIC?
3. **RQ3 — unminimized inputs:** does the approach still work when fuzzer-generated programs are not reduced first?
4. **RQ4 — practical cost:** how expensive is the required compiler-history exploration?

The current arXiv v3 reports evaluation on five datasets: GCC 4.3.0 (1,235 programs / 29 bugs), GCC 4.4.0 (647 / 11), GCC 4.5.0 (26 / 7), LLVM 2.8.0 (80 / 5), and a newly constructed GCC 13.1.0 set (42 / 7). It reports average human-effort savings of **33.56% vs Tamer** and **10.68% vs D3** for identifying the same number of distinct bugs.

## Reproduction level

**Current level: L1 partial + scoped L2 mechanism validation.**

- **L1 partial:** the released GitHub artifact is pinned and its published prioritization results are recomputed with `evaluate.py`; RQ4 is rerun with `rq4.py`.
- **Scoped L2:** `live_bisect_smoke.sh` creates a fresh Git history, introduces two independent synthetic compiler regressions, runs real `git bisect run` on three distinct test cases, and verifies that two cases with the same first-bad commit cluster together while the third is separated.
- **Not L2 on the paper datasets:** this run does not rebuild historical GCC/LLVM revisions and execute every bug-triggering program through a fresh bisection campaign.
- **Not L3:** the five-dataset paper-scale experiment is not rerun end to end.

## Important reproducibility gap found

The **current paper v3 says five datasets**, including GCC 13.1.0. The public GitHub artifact pinned above currently exposes only the four historical datasets, and its `evaluate.py` enumerates only `gcc430`, `gcc440`, `gcc450`, and `llvm280`. No `gcc131`/GCC-13.1 dataset is present in that repository.

This matters because the current paper abstract/conclusion uses the five-dataset result (**33.56% / 10.68%** effort savings), while the released GitHub artifact can only independently regenerate the older four-dataset tables. `audit_artifact.py` makes this discrepancy machine-checkable instead of silently treating the artifact as a full v3 reproduction.

## How to run

```bash
cd papers/2026-buglens
./reproduce.sh
```

Outputs are written to `results/`:

- `table2.txt` — recomputed BugLens/Tamer/D3 effort curves and Wilcoxon p-values from released results;
- `rq4.txt` — released RQ4 compiler-version-count / average-cost evidence;
- `artifact-audit.json` — dataset/claim coverage audit;
- `live-bisect-smoke.txt` — fresh git-bisection mechanism validation.

## Paper vs. this reproduction

| Question | Paper | This repository | Status |
|---|---|---|---|
| Does bisection provide a useful dedup signal? | Real compiler histories + real bug datasets | Fresh synthetic history using real `git bisect run` | scoped L2 support |
| Does BugLens beat Tamer/D3? | Five datasets in current v3 | Recompute released four-dataset ordering files | L1 partial |
| Does it work without minimization? | Real unminimized GCC inputs | Released RQ3 files are present but not regenerated from compiler executions | L1 evidence only |
| Is it cheap? | Compiler-history measurements | `rq4.py` reprocesses released measurements | L1 |
| GCC 13.1.0 generalization | 42 programs / 7 bugs | Dataset absent from public GitHub artifact used here | blocked |

## Experiment design for L3

A faithful paper-scale rerun should freeze five dimensions:

1. **Compiler history:** exact GCC/LLVM repositories and commit ranges, including merges/reverts.
2. **Subjects:** all five bug datasets and the exact good/bad version boundary for each test.
3. **Oracle:** deterministic wrong-code checker, with UB filtering matching the paper.
4. **Baselines:** Tamer and D3 with the same minimized/unminimized inputs and the same prioritization budget.
5. **Statistics:** repeated prioritization trials, effort-to-k-bugs curves, paired tests/effect sizes, wall-clock compiler build + test cost, and cache hit rates.

For CI, historical compiler builds should live on a self-hosted runner or prebuilt OCI images. GitHub-hosted CI should remain a deterministic audit/smoke lane.

## Threats / failure modes worth testing

- **Non-monotonic history:** a bug can appear, disappear, and reappear due to reverts or interacting passes; ordinary bisection assumes a monotonic good→bad boundary.
- **Merge topology:** first-bad SHA is not a stable semantic identifier across rebases/backports/cherry-picks.
- **Commit co-location:** one large commit can introduce multiple unrelated regressions; optimization-name splitting may still be too coarse.
- **Oracle instability:** flaky wrong-code reproduction changes the bisection path and can create bogus clusters.
- **Historical confounding:** four of the five datasets are very old GCC/LLVM releases; engineering practices and commit granularity have changed.
- **Cost accounting:** build caches can make bisection cheap in one environment and expensive in another; human-effort savings should be reported alongside compute cost.

## Extensions that could become a new result

### 1. Patch-semantic BugLens

Replace raw FIC SHA with a normalized change identity: patch-id + touched compiler pass/functions + optimization family. Evaluate robustness under cherry-pick/backport/rebase. This directly attacks the weakness that commit hashes are repository-history identifiers, not bug identities.

### 2. Non-monotonic / flaky bisection

Use repeated execution and probabilistic interval search when the failure predicate is noisy or non-monotonic. Compare dedup precision/recall against standard `git bisect`.

### 3. Modern compiler CI integration

Run on recent LLVM/GCC fuzz regressions and measure **time-to-first-distinct-bug**, not only number of test cases examined. This is closer to how a compiler team would consume the technique in continuous fuzzing.

### 4. BugLens + reducer scheduling

Use dedup clusters before reduction: reduce only one representative per predicted cluster, then expand when evidence suggests a false merge. Measure total reducer CPU-hours saved and bug-slippage risk.

## Blocker to the next level

The immediate blocker for a full v3 reproduction is the missing public GCC 13.1.0 dataset / corresponding fresh bisection metadata in the GitHub artifact used here. The historical compiler-scale rerun also needs prebuilt GCC/LLVM revision images or a persistent self-hosted runner; rebuilding hundreds of revisions on ephemeral Actions runners is unnecessarily expensive.

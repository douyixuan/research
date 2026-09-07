# OPERA — A Tale of Two DL Cities: When Library Tests Meet Compiler

Paper: Qingchao Shen, Yongqiang Tian, Haoyang Ma, Junjie Chen, Lili Huang, Ruifeng Fu, Shing-Chi Cheung, Zan Wang. ICSE 2025. arXiv:2407.16626.

Official artifact: `ShenQingchao/OPERA`, pinned here to commit `926ea4315c86c35dcfdcd80a2c6b2a7ac9c07cf7`.

## Core insight

DL compiler frontend testing and DL-library operator testing share the same semantic unit: an operator plus parameter settings. OPERA migrates operator instances from library tests into single-operator compiler models, then prioritizes them using two dimensions: (1) operator signatures that are common in library tests but underrepresented in compiler tests, and (2) parameter-subspace novelty. The paper evaluates eight frontends across TVM 0.13, TensorRT 8.6, and OpenVINO 2023.1.0.

## Reproduction level

**L1 reported-results (APFD) + L0 artifact audit + scoped L2 prioritization mechanism.**

This is not L3 and must not be described as a full reproduction. The historical full stack requires PyTorch 1.7, Keras 2.3, ONNX 1.8, TVM at `b48fcab`, TensorRT 8.6, OpenVINO 2023.1.0, the original migrated model corpus, and long compiler executions. The deterministic CI lane instead reprocesses the released APFD fault-rank data and runs a fresh minimal control-logic experiment.

## What is actually run

`./reproduce.sh` performs two independent experiments.

1. `reproduce.py` downloads only the pinned official artifact files `analyze_results/cal_APFD_all.py` and `bugs.md`. It AST-parses the released fault-rank dictionaries, independently recomputes APFD for all eight frontend subjects and all five prioritization strategies, averages them, and checks the paper's reported `0.898` mean APFD plus the `13.1% / 11.9% / 47.4% / 37.2%` improvements over random / FAST / total-coverage / additional-coverage baselines.
2. `mini_tcp.py` performs a fresh, deterministic, synthetic end-to-end run of the prioritization control mechanism: operator-signature gap × parameter-subspace novelty with iterative novelty updates. This is a scoped L2 mechanism reproduction only; it does not claim to reproduce compiler bug discovery.

Outputs are written to `results/` and uploaded by GitHub Actions.

## Paper vs reproduction

| Claim | Paper | This reproduction |
|---|---:|---:|
| Mean APFD of OPERA | 0.898 | **0.897619** |
| Improvement vs random | 13.1% | **13.0855%** |
| Improvement vs FAST | 11.9% | **11.9037%** |
| Improvement vs total coverage | 47.4% | **47.3980%** |
| Improvement vs additional coverage | 37.2% | **37.1985%** |
| Previously unknown bugs | 170 | L0 only; no paper-scale rerun |
| Confirmed/fixed at paper time | 90 | Pinned artifact ledger: **102** |
| Frontend bug-finding effectiveness | 8 frontends, historical versions | Not rerun |

All five APFD aggregate claims reproduce to the paper's displayed precision. The 102-vs-90 difference is treated as provenance/status drift, not as a failed reproduction: the paper states 90 confirmed/fixed at evaluation time, while the later artifact ledger explicitly states 102 confirmed/fixed.

### Scoped L2 result

The fresh synthetic prioritization run produced APFD **0.58333** versus **0.52778** for a deterministic alphabetical baseline (`+0.05556`). It exercises the priority/update loop but is intentionally too small and synthetic to support any claim about the paper's compiler bug-finding effectiveness.

## Threats and limitations

The L1 result depends on released fault ranks rather than re-executing tests, so it validates analysis arithmetic but not test generation, migration, model loading, deduplication, or bug triage. The scoped L2 experiment uses synthetic operator instances and therefore validates only the stated prioritization mechanism. Historical dependency versions are old enough that a modern rerun risks conflating OPERA behavior with PyTorch/ONNX/TVM/OpenVINO/TensorRT drift. TensorRT also introduces platform/GPU and packaging constraints.

## Best next experiment — L4 frontend-drift matrix

Re-run the same migrated operator-instance corpus against **paper-era vs current TVM/OpenVINO frontends**, while keeping test order and oracle budget fixed. Classify each old failure as `still fails / fixed / unsupported-now / semantic-drift / oracle-drift`, and add newly exposed failures. Then compare OPERA prioritization with random and a modern coverage/embedding baseline under equal wall-clock and test-count budgets.

This directly measures whether the paper's advantage survives compiler/frontend evolution rather than merely reusing old fault ranks. A second ablation should separate operator-signature score from parameter novelty on current frontends, since the original paper reports APFD `0.613` for operator-only, `0.832` for parameter-only, and `0.898` for both.

## Promotion criteria

- **L2 frontend run:** execute at least one released migrated model through one pinned compiler frontend and its source-library oracle.
- **L3:** recreate the eight-subject evaluation with comparable historical versions/budgets and repeat randomized prioritization runs five times.
- **L4:** add the toolchain-drift matrix or a fair modern baseline under a fixed budget.

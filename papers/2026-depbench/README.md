# DEPBENCH — Update from Hell: Can Coding Agents Survive Hidden Breakage in Dependency Upgrades?

- Authors: Zijian Luo, Runzhi He, Pengfei Gao, Yu Kang, Zeqi Lin, Minghua Ma, Qingwei Lin, Saravan Rajmohan, Yongqiang Tian
- arXiv: 2608.30300, submitted 2026-08-31
- Paper: https://arxiv.org/abs/2608.30300
- Current reproduction level: **L0 claim/artifact audit + scoped L2 case reconstruction**

## Core insight

A dependency update is not reliably solved just because the repository's visible tests are green. DEPBENCH isolates dependency-upgrade repair with a four-state oracle that separates the base repository, dependency manifest/lockfile change, developer repair, and held-out test patch. The strongest reported completed configuration solves only 104/203 tasks (51.2%), and incomplete repository-wide migration is the dominant agent-side failure mode.

The benchmark contract for base state `b`, manifest patch `m`, repair patch `c`, test patch `t`, and verifier `Omega` is:

1. `Omega(b) = pass`
2. `Omega(b + m + t) = fail`
3. `Omega(b + m + c + t) = pass`
4. `Omega(b + c + t) = fail`

This is stronger than ordinary "upgrade + run existing tests" evaluation because it checks that the hidden failure is caused by the upgrade and that the repair is both necessary and sufficient under the task oracle.

## Public-artifact audit

As of 2026-09-03, the arXiv record exposes the paper and links the Harbor evaluation harness, but no official DEPBENCH dataset/repository or raw trajectory/result artifact was located via the arXiv code/data section or public GitHub repository search. Therefore:

- **L1 is not claimed**: there are no located official raw result files to reprocess.
- **L3 is not claimed**: the 203 released task containers, held-out patches, verifier scripts, and full agent trajectories are not publicly located in this audit.
- The paper does provide a concrete public representative case, `harvard-lil/js-wacz#41`, which can be independently reconstructed from the upstream Git history. That case is used for the scoped L2 lane below.

Required to advance to L1/L3: official task metadata, task/container images or build recipes, held-out test patches/verifiers, and raw per-configuration outcomes/trajectories; L3 additionally requires the paper-scale Harbor environment and model/harness access under the stated 30-minute agent + 5-minute verifier budgets.

## What is reproduced here

### L0: arithmetic and consistency audit

`audit_claims.py` checks paper-transcribed values only. This is deliberately **not L1**.

Validated invariants include:

- ecosystem task counts: `68 + 65 + 40 + 20 + 10 = 203`;
- Codex + GPT-5.5 ecosystem passes: `27 + 46 + 20 + 6 + 5 = 104`;
- best reported pass rate: `104 / 203 = 51.2%`;
- GPT-5.5 Codex vs Claude Code spread: `104 - 71 = 33` tasks = `16.3` percentage points;
- visible-test-pass paradox: `322 / 521 = 61.8%` of analyzed non-pass trajectories;
- primary direct-behavior held-out tests: `156 / 203 = 76.8%`.

### Scoped L2: live reconstruction of the paper's js-wacz example

The paper explicitly uses `harvard-lil/js-wacz#41`, upgrading `glob` 8.1.0 -> 10.3.3, as its patch-decomposition example. The upstream PR has two commits:

- base: `167febc84b6183c4c971e5aec743e79406a4f847`
- dependency/manifest update: `857cbdec952f14b9116c093b89aa62034ae6aa23`
- human ESM repair: `12fe776401cfc219a32d49573d1505acc4063708`

`live_jswacz_oracle.sh` clones the real upstream repository and reconstructs:

- `m` from the dependency commit's `package.json` and `package-lock.json` changes;
- `c` from the human commit's `index.js` change;
- `t` from the same human commit's `index.test.js` change.

It then runs `npm ci && npm test` independently for all four states and asserts the expected pass/fail vector.

This is a **scoped L2 case reconstruction**, not an official DEPBENCH release-task replay, because the official benchmark's exact packaged hidden-test task artifact is not publicly located here. It still uses the real repository, real dependency upgrade, and real upstream repair from the paper's concrete example rather than a synthetic mechanism simulation.

## Observed run — 2026-09-03

GitHub Actions run `33702887802` completed successfully on Ubuntu 24.04.4 with Node 20.20.2 / npm 10.8.2. The live oracle produced exactly the required state vector:

| State | Expected | Actual |
|---|---|---|
| `b` | pass | pass |
| `b + m + t` | fail | fail |
| `b + m + c + t` | pass | pass |
| `b + c + t` | fail | fail |

`four_state_oracle_satisfied = true`. The workflow uploaded 8 result/log files as artifact `9874153649` (9,314 bytes; SHA-256 `f3e696a9366dd10fa2b61799fc24c32c6273f73b1293809eeef1d3fbfac78385`).

The runner also warns that several pinned GitHub `actions/*` majors still target the deprecated Node 20 action runtime and are currently forced to Node 24 by GitHub. This does not affect the explicitly installed Node 20 used for the js-wacz experiment, but it is recorded as CI/toolchain drift rather than hidden.

## Experiment design

The CI lane has two parts:

1. deterministic paper-claim arithmetic audit with Python 3.12;
2. live real-repository four-state oracle on Ubuntu 24.04 + Node 20.

Generated logs and JSON summaries are uploaded as a GitHub Actions artifact. The live lane is intentionally allowed to reveal ecosystem drift: historical npm lockfiles, registry availability, Node behavior, or transitive dependency changes can break the reconstruction. Such drift is a result to record rather than silently paper over.

## Paper vs reproduction

| Item | Paper | This reproduction |
|---|---:|---|
| Benchmark size | 203 tasks | arithmetic check only; official task release not located |
| Ecosystems | 68 npm, 65 Maven, 40 Go, 20 Cargo, 10 Python | counts sum to 203 |
| Best completed config | Codex + GPT-5.5: 104/203 (51.2%) | arithmetic check matches |
| Visible tests green before hidden failure | 322/521 (61.8%) | arithmetic check matches |
| Full 203-task agent evaluation | yes | not reproduced |
| Four-state oracle | all release tasks | live public-case reconstruction: pass/fail/pass/fail matched |
| Raw official result reprocessing | paper reports results | unavailable; therefore no L1 claim |

## Threats and limitations

- The js-wacz test patch is reconstructed from the public PR's test-file change, not fetched from an official DEPBENCH release artifact.
- A single npm case cannot support conclusions about the 203-task benchmark, cross-ecosystem behavior, model ranking, or harness ranking.
- The live reproduction runs on a modern GitHub-hosted runner, not the paper's pinned task image. Toolchain/registry drift can affect results.
- No model is invoked in the default CI lane, so this does not reproduce agent repair success rates.
- Paper-table arithmetic checks are transcription consistency checks, not evidence equivalent to reprocessing raw experiment outputs.

## Most valuable extension (L4 proposal)

**Post-cutoff contract-propagation ablation.** Build a fresh dependency-upgrade slice whose dependency releases and repair PRs occur after the evaluated model's training cutoff, then compare under the same model, wall-clock and token/API budget:

1. standard coding-agent harness;
2. standard harness + mandatory repository-wide usage search after identifying a breaking symbol/type;
3. standard harness + structured API-diff / migration-guide retrieval;
4. both propagation search + structured upstream evidence.

Measure hidden-test pass rate, visible-test false-confidence rate, incomplete-migration frequency, wall-clock, tool calls, tokens/API cost, and changed-file recall relative to the developer repair. This directly tests whether DEPBENCH's dominant failure is improved by better contract propagation rather than by model memorization or simply larger budgets.

A second useful analysis is leave-one-ecosystem-out calibration: normalize each harness by equal wall-clock/tool-call budget and compare whether the paper's Maven advantage remains after controlling for build-system feedback strength.

## Run

```bash
bash papers/2026-depbench/reproduce.sh claims
bash papers/2026-depbench/reproduce.sh live
# or both
bash papers/2026-depbench/reproduce.sh all
```

CI: `.github/workflows/paper-depbench.yml`.

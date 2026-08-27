# RepoTrace: Browser-Assisted Evidence Collection for GitHub Research Datasets

- Authors: Xue Yao, Zehua Zhang, Jiatong Liu, Yongqiang Tian
- Venue/status: SPLASH/ISSTA 2026 Tool Demonstration; arXiv:2607.05106
- Paper DOI: `10.1145/3837729.3840498`
- Artifact: https://github.com/t3-research/RepoTrace
- Artifact snapshot used here: `60e59177dd0a1621108c3b1aaeb2a93e447f0a3e`
- Current reproduction level: **L0 artifact audit + scoped L2 live-minimal**

## Core insight

RepoTrace treats a GitHub issue/PR as both a changing source document and a research object. Instead of separating browser evidence, spreadsheet labels, reviewer rationale, and later refreshes, it keeps them in one local SQLite-backed provenance model. The architecture is a Chrome side-panel collector -> Express backend -> SQLite -> React dashboard.

The interesting research claim is not a performance win. It is **traceability**: source evidence, coding decisions, reviewer disagreement, refresh history, and exports remain connected enough that a manually curated GitHub dataset can be audited later.

## Paper experiment

The paper demonstrates the workflow on 20 `matplotlib/matplotlib` issues split across two projects. Reported totals are:

| Measure | Paper |
|---|---:|
| Records | 20 |
| Snapshots | 22 |
| Captured comments | 38 |
| Research notes | 20 |
| Research annotations | 98 |
| Screening reviews | 20 |
| Fix-evidence entries | 20 |
| Simulated unresolved consensus conflicts | 4 |
| Automated tests | 37 passing |

The four conflicts are synthetic workflow fixtures, not observed reviewer disagreement.

## What this reproduction actually runs

`reproduce.sh` checks out the exact public artifact snapshot and runs:

1. `npm ci`
2. `npm test`
3. `npm run typecheck`
4. `npm run build`
5. `npm run db:seed-demo` against a fresh SQLite database
6. a live Express server
7. `/health`, full JSON export, and project-backup API calls
8. an audit of whether the public snapshot contains the paper-aligned validation files named by `REPRODUCIBILITY.md`

This is **scoped L2** because real upstream source, database initialization, tests, build, server, and export paths are rerun from scratch. It is not L3: browser collection against live GitHub pages and the full 20-record Matplotlib validation are not rerun.

## Paper vs reproduction

| Claim / evidence | Paper | Ours | Level |
|---|---|---|---|
| Source builds | yes | rerun in CI | L2 scoped |
| Automated suite | 37 tests pass | asserted from fresh Vitest run | L2 scoped |
| SQLite demo seed | representative workflow data | fresh DB created | L2 scoped |
| Backend health/export/backup | supported | live API calls executed | L2 scoped |
| 20-record validation totals | 20 / 22 / 38 / 20 / 98 / 20 / 20 / 4 | **not recomputed** | L0 audit |
| Browser extraction on current GitHub DOM | supported | not exercised headlessly | not reproduced |

## Reproducibility gap found

The public GitHub snapshot's `README.md` and `REPRODUCIBILITY.md` refer to `paper/supporting/VALIDATION_NOTES.md`; the reproducibility packaging checklist also names `paper/` and `PROJECT_PLAN.md`. The current public GitHub tree at the pinned initial release contains neither `paper/` nor `PROJECT_PLAN.md`.

That matters because the seeded demo is explicitly documented as **not** being the full 20-record Matplotlib validation dataset. Therefore the paper's Table 2 totals cannot be honestly called L1 from the GitHub snapshot alone. The Zenodo record (`10.5281/zenodo.20954131`) may contain a fuller archived package and is the next artifact to audit before claiming L1.

## Threats / limitations

- GitHub DOM drift can break extraction while backend/unit tests still pass.
- The deterministic demo seed validates data-shape and workflows, not the manually checked 20-record study.
- Live GitHub API refresh is intentionally excluded from CI because it adds token/rate-limit/network nondeterminism.
- A tool-demo validation is not a user study; it shows workflow completeness, not researcher productivity or labeling quality.
- Multi-reviewer conflicts in the validation are injected, so they do not establish real-world consensus effectiveness.

## Best extension: provenance survival under source drift

A stronger study would measure **provenance survival under GitHub evolution**.

Take a timestamped corpus of issues/PRs, collect them once, then replay realistic mutations: edited body, deleted/edited comments, relabeling, close/reopen, linked PR changes, and DOM-layout changes. Compare:

- spreadsheet + URL baseline,
- GitHub API snapshot baseline,
- RepoTrace browser snapshot + refresh history.

Metrics:

- evidence-recovery rate after source changes,
- percentage of research labels whose rationale still resolves to preserved evidence,
- false/true update-detection rate,
- reviewer time to re-audit a record,
- export/backup round-trip fidelity.

This tests the central provenance claim more directly than counting stored rows.

## Additional extensions

1. **Real multi-reviewer study** — Cohen/Fleiss agreement plus time-to-consensus, rather than synthetic conflict injection.
2. **DOM-drift regression corpus** — archived GitHub HTML from multiple dates to quantify extractor fragility.
3. **Dataset-as-code baseline** — compare RepoTrace with JSON/YAML + git history + GitHub API scripts, not only spreadsheets.
4. **Content-addressed evidence** — hash snapshots/comments and include hashes in exported annotations so provenance can be independently verified.
5. **Research CI integration** — fail a dataset build when referenced evidence disappears, changes, or loses reviewer consensus.

## Moving to L1 / L3

To reach **L1**, obtain the complete paper-era validation package (preferably the Zenodo snapshot), then recompute the 20-record Table 2 counts directly from its data/notes rather than copying paper numbers.

To reach **L3**, automate a Chromium run that loads the extension, collects the paper's 20 Matplotlib issues (or an archived equivalent), performs the documented review/export workflow, and compares the resulting provenance-bearing dataset with the paper-era validation snapshot.

## Run

```bash
bash papers/2026-repotrace/reproduce.sh
```

Generated evidence is written under `papers/2026-repotrace/results/` and uploaded by GitHub Actions.

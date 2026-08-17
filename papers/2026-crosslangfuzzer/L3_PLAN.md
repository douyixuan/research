# L3 plan — paper-scale CrossLangFuzzer reproduction

The current CI lane is intentionally a scoped L2 live reproduction of one reported bug. Advancing to L3 means rerunning the **actual search pipeline**, not replaying known triggers.

## Pinning

Use the archived paper artifact when possible:

- Zenodo: https://doi.org/10.5281/zenodo.20925432
- For a modern artifact-build comparison, pin GitHub commit `d3ebc126aec6e31bfb561d5a672b3eecf53b15c6` (2026-08-09), but do not substitute it for the archival paper snapshot when claiming paper-scale reproduction.

Record all of:

- artifact commit/snapshot;
- JDK 8/11/17 builds;
- Kotlin/Groovy/Scala/Javac versions;
- Gradle lock/dependency resolution;
- host CPU, RAM, runner image;
- random seeds and wall-clock budget.

## Staged experiment

### Stage A — artifact integrity

1. Build the official project with JDK 11.
2. Install the JDK 8 and 17 runtimes required by the Kotlin runner.
3. Execute official unit tests.
4. Run each language printer on fixed IR fixtures.
5. Verify generated programs compile under at least one expected compiler configuration.

Acceptance: clean build + deterministic fixture hashes + no untracked dependency failures.

### Stage B — generator/mutator smoke

Run short fixed-seed campaigns for Kotlin/Java, Groovy/Java, Scala/Java.

For every generated case record:

- seed;
- serialized IR before/after mutation;
- language assignment;
- mutation sequence;
- emitted source;
- compiler versions;
- exit/status/diagnostics;
- reducer result when divergence is found.

Acceptance: at least 1,000 compilations per language pair without harness failure; every candidate divergence is replayable from stored IR.

### Stage C — causal ablation

Hold generated IR constant and compare:

1. no mutation;
2. semantic mutations without `shuffleLanguage`;
3. `shuffleLanguage` only;
4. full CrossLangFuzzer.

Primary metrics:

- unique candidate divergences / 1k compilations;
- confirmed/replayable divergences;
- boundary-specific coverage;
- time-to-first divergence;
- reducer success rate and reduced size.

This is more diagnostic than simply comparing raw bug counts.

### Stage D — paper-like campaign

Run repeated campaigns at a fixed compute budget for each supported compiler family. Use a minimum of 10 seeds for an engineering reproduction; increase toward the paper's original campaign budget if archival instructions provide one.

Do **not** count diagnostics as unique bugs directly. Cluster candidates by minimized reproducer, failing compiler path/stack trace, and issue/root-cause evidence.

Report:

- total compilations;
- valid generated programs;
- candidate divergences;
- minimized reproducible divergences;
- unique root-cause clusters;
- confirmed known/new bugs;
- CPU-hours and compiler invocations per confirmed bug.

### Stage E — prospective extension

Repeat on compiler versions released after 26 June 2026. The primary extension should be a **bug survival + new-discovery matrix**:

| Trigger / generated pattern | paper-era version | current stable | newest pre-release | classification |
|---|---|---|---|---|
| ... | fail/pass | fail/pass | fail/pass | survives / fixed / regressed / new |

This separates historical reproducibility from present-day research value.

## Baselines

A fair baseline should be matched on compiler invocations and wall-clock/CPU budget, not just elapsed campaign duration. At minimum compare:

- CrossLangFuzzer with cross-language placement;
- same generator constrained to a single source language;
- CrossLangFuzzer without `shuffleLanguage`;
- if a compatible external generator is available, an established JVM compiler fuzzer under the same compilation budget.

## Statistics

For repeated campaigns, report distributions rather than only totals:

- median + IQR for time-to-first candidate/confirmed bug;
- bootstrap confidence intervals for unique root causes per budget;
- survival curves for time-to-first finding;
- effect sizes for ablations;
- duplicate rate before/after reduction/clustering.

## Blockers / resources

L3 is resource-bound rather than conceptually blocked:

- JDK 8 + 11 + 17 must coexist;
- long fuzz campaigns do not fit comfortably in ordinary GitHub-hosted CI quotas;
- some historical compiler versions and dependencies must be pinned;
- confirmation of genuinely new bugs requires manual triage and upstream reporting.

Recommended execution: GitHub-hosted Actions for Stage A/B; self-hosted runner for Stage C/D/E. Store minimized reproducers and aggregate results as Actions artifacts, not raw multi-hour logs in git.

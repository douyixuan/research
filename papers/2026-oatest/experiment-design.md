# OATest reproduction and extension design

## L2: one live historical TVM bug

Target the paper/artifact's `StaticPlanBlockMemory` + `DataflowBlock` failure (TVM #17488). The public issue contains a small Relax program and the fixing PR #17501 was merged as `3d966230caa63b4ad8c3d6c86aaad27d5a8a0918`.

Matrix:

| Revision | Purpose | Expected result |
|---|---|---|
| vulnerable ancestor / paper-era revision | demonstrate original failure | `StaticPlanBlockMemory` crashes with the reported internal error |
| merge commit `3d966230...` | validate fix boundary | program completes without the reported internal error |
| current TVM main | drift check | no regression; record any API migration needed |

Acceptance criteria:

1. exact optimization pass is invoked, not a proxy test;
2. vulnerable and fixed revisions run from the same minimized program or explicitly documented migrated equivalents;
3. logs capture compiler SHA and exception/result;
4. a changed API is not counted as a compiler-bug fix.

Because old TVM source builds are expensive for hosted CI, this should be a cached or self-hosted lane rather than blocking the cheap L1 audit.

## L3: paper-scale reproduction

Pin the paper subjects:

- TVM `292ecfd`;
- ONNXRuntime `5c1b7cc`;
- official OATest artifact commit `20d7464201f35c0552777cf7de4d696cb7b1ecd1`.

Recreate the released pattern corpus and seed pool, then run OATest and paper baselines under the same resource envelope. The main effectiveness comparison should use **12-hour campaigns × 5 independent repetitions** per compiler/technique, with random seeds recorded.

Record for every run:

- valid generated tests / second;
- target-optimization trigger rate;
- optimization-code branch and line coverage;
- unique deduplicated bugs;
- time-to-first bug and time-to-each-new bug;
- generator time as fraction of total fuzzing time;
- peak RAM/GPU usage;
- LLM token/API cost for LLM baselines, if those baselines are rerun.

Fairness controls:

- identical compiler builds, hardware quotas and fuzzing wall time;
- identical initial seed pools where the method permits it;
- five independent seeds, with median/IQR plus raw runs rather than only means;
- same deduplication rule across techniques;
- pin the exact LLM/model revision for model-based baselines; current replacements are an extension, not a faithful baseline reproduction.

## L4-A: pass-conditioned context selection

Hypothesis: after obtaining a known optimization-triggering pattern, selecting contexts/injection sites that are semantically or coverage-wise related to the target pass improves exploration efficiency over random synthesis choices.

Compare:

1. OATest original selection;
2. static feature retrieval (op types, shapes, dtypes, graph topology);
3. coverage-guided selection using historical pass-edge novelty;
4. hybrid retrieval + coverage.

Primary metric:

`optimization-triggered new branch edges / 1,000 valid tests`

Secondary metrics: target-pass trigger rate, unique bug count, valid-test rate, generation latency, diversity of graph contexts.

A useful result is not merely higher total coverage: the extension should show that the extra coverage occurs inside or downstream of the intended optimization and is obtained at comparable generation cost.

## L4-B: compiler-version drift benchmark

For each released OATest bug seed/minimized reproducer, build a timeline over:

`paper-era → fix commit (if known) → stable releases → current main`

Classify each point as:

- reproduces same bug;
- fixed;
- regression after fix;
- test invalid because IR/API changed;
- pass removed/renamed;
- behavioral change requiring investigation.

Use merged fix PR/commit ancestry as fix provenance. Do not equate an open issue with an unfixed bug; TVM #17488 is an example where the issue remains open although PR #17501 was merged.

## L4-C: oracle sensitivity

Rerun inconsistency candidates using multiple oracle policies:

- paper tolerance;
- dtype-aware absolute/relative tolerance;
- ULP-aware comparison;
- operation-conditioned tolerance for numerically unstable ops;
- metamorphic checks where a valid relation exists.

Report the overlap matrix of bug candidates. This quantifies how much OATest's apparent effectiveness depends on the numerical oracle rather than the test generator.

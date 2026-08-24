# Experiment design

## RQ-A — Can released evidence regenerate the displayed Siemens comparison?

**Input.** Official artifact snapshot `43c2f12306f02582779b24766dbddeadce9480e3`, specifically `benchmarks/Siemens/result-summary-*.txt`.

**Procedure.** Parse each `(faulty version, test case)` record; for each paper-defined best MR, intersect DDMT and ddmin keys so both methods are compared on exactly the same subject/input pair; compute arithmetic means for final input size, query count, and wall time; compare with Table VI at its displayed precision.

**Acceptance.** Every released best-MR row matches the displayed table after rounding. Missing evidence is reported as an artifact gap rather than silently ignored.

## RQ-B — Does oracle-less MR-guided reduction work end-to-end?

**Input.** A fresh six-element textual input containing one trigger element.

**Target.** A deterministic tokenizer with a seeded silent bug.

**MR.** Adding a trailing comment should preserve token analysis.

**Reducer predicate.** `FAIL` iff source and follow-up outputs violate the MR. No expected output or correct implementation is passed to the reducer.

**Acceptance.** The oversized input is reduced to the one-element trigger while the MR remains violated.

## RQ-C — Extension: can adaptive MR choice improve cost-adjusted reduction?

Compare four policies on identical seeds and budgets:

1. fixed MR selected a priori;
2. random MR;
3. round-robin MR portfolio;
4. adaptive bandit choosing the MR with highest recent `reduction_gain / target_execution_cost`.

Report final size, number of reducer candidates, total target executions (not just `mrtest` calls), wall time, MR-violation yield, and variance over repeated runs. This avoids the unfair comparison where one DDMT query is counted like one ordinary `test` even though it normally requires two target executions plus MR generation/checking.

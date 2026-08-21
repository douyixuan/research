# Runtime results

`reproduce.sh` recreates `results/runtime/` on every run. GitHub Actions uploads that directory as `erwin-reproduction-report`.

Expected files include generated Solidity programs for `type`, `loc`, and `scope` bounded-exhaustive lanes, generator logs, compile-failure logs, tool versions, `summary.json`, and `summary.md`.

Generated runtime output is intentionally not committed because Erwin's released CLI is stochastic; the CI artifact is the evidence for each run.

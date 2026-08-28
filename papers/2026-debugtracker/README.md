# DebugTracker: Lightweight Process Evidence for Classroom Debugging

- Authors: Jiatong Liu, Xue Yao, Zehua Zhang, Yongqiang Tian
- Venue: SPLASH/ISSTA 2026 Tool Demonstrations
- arXiv: https://arxiv.org/abs/2607.05871
- DOI: https://doi.org/10.1145/3837729.3840500
- Official artifact: https://github.com/t3-research/DebugTracker
- Archived artifact: https://doi.org/10.5281/zenodo.20955037
- Pinned GitHub snapshot: `72798f7f148c4d58ae36055849276cb5571e4047`

## Status

**L0 artifact audit + scoped L2 live-minimal.**

This reproduction freshly rebuilds and tests the extension, rebuilds its VSIX, audits the paper-visible validation structure, and reruns the shared TypeScript/Python/Java debugging task before and after the documented fix. It does **not** automate the full 11-case GUI/manual matrix across three operating systems, so it is not L3 and is not presented as full paper reproduction.

## Core insight

A final patch says little about *how* a student debugged. DebugTracker treats debugging as a process-evidence problem: normal IDE/test/debugger activity is normalized into an append-only event stream, and timeline/report views are derived from that stream. The design deliberately separates:

- **Evaluation Mode** — uncoached evidence collection for assessment;
- **Training Mode** — process nudges and optional AI feedback;
- **human labels** — instructor judgments appended separately from the original trace.

The interesting systems idea is the single-source-of-truth event log: reports and timelines are derived views rather than mutable independent records.

## Paper validation claims targeted here

The paper validates the prototype with:

1. **16 automated checks** covering session IDs, terminal-test detection, mode policy, report generation, AI-coach prompt construction, image/source evidence, timeline/session views, human labels, and training feedback;
2. an **11-case manual trial matrix** covering VSIX installation, Evaluation/Training flows, TypeScript/Python/Java, Windows/macOS/Linux wrappers, AI Coach, image evidence, reviewer export, and missing-debugger behavior;
3. one deliberately shared checkout-pricing bug across the three languages, where shipping eligibility incorrectly uses the original subtotal instead of the discounted/taxable subtotal.

The automated 16 and documented manual 11 are auditable in the pinned artifact. CI reruns the automated suite and the language task behavior, but only audits—not executes—the full GUI/manual matrix.

## Reproduction design

Run:

```bash
bash papers/2026-debugtracker/reproduce.sh
```

The script:

1. clones the official artifact and checks out the pinned snapshot;
2. statically audits the 16 automated-test calls and 11 documented manual cases;
3. runs `npm ci && npm test` from scratch;
4. rebuilds the VSIX and records hashes/package contents;
5. runs the buggy TypeScript/Python/Java checkout-pricing tasks and requires each to fail;
6. applies only the documented one-line shipping-basis fix in each language and requires each task to pass;
7. writes all evidence under `results/`.

GitHub Actions supplies pinned Node/Python/JDK environments so the cross-language smoke test is repeatable.

## Paper vs reproduction

| Claim / property | Paper | This reproduction |
|---|---|---|
| Automated validation | 16 checks pass | Fresh upstream suite + structural count audit |
| Manual validation | 11 cases across packaged VSIX and three OSes | Matrix count audited only; GUI/manual cases not fully executed |
| Cross-language task | TypeScript, Python, Java share the same intended bug | Fresh fail-before / pass-after execution for all three languages |
| Packaged extension | Prebuilt `debug-tracker-0.1.0.vsix` | Fresh VSIX build; hash recorded, binary identity not assumed |
| Evaluation vs Training separation | Explicit mode policy | Covered by upstream automated suite, not a human UI trial here |
| Classroom assessment benefit | Future work / not established by this tool-demo validation | Not claimed |

## Why this is scoped L2 rather than L1

The useful evidence here comes from **fresh execution** of the artifact and sample tasks, not merely reprocessing saved outputs. That is L2-style evidence. However, the fresh run is deliberately smaller than the full paper validation because GitHub-hosted CI does not reproduce interactive VS Code workflows or the full Windows/macOS/Linux manual trial matrix.

## Blockers to L3

A faithful L3 should execute the published 11-case matrix with the packaged VSIX. That requires:

- VS Code GUI/Extension Host automation or a stable integration-test harness;
- Windows, macOS, and Linux runners;
- Java/Python debugger extensions for breakpoint cases;
- clipboard/image automation for image-evidence cases;
- a mock OpenAI-compatible endpoint for deterministic AI-Coach testing;
- explicit assertions over generated JSONL, snapshots, reports, and reviewer output.

No API key is required for the current reproduction because remote AI feedback is optional and disabled.

## Threats / limitations

- Upstream unit tests are written by the artifact authors, so passing them demonstrates implementation consistency, not independent correctness.
- The shared three-language task is intentionally small; it supports language-agnostic plumbing but not general language independence.
- The 11 manual cases are documented acceptance tests rather than a controlled user study.
- Rebuilding a VSIX does not imply byte-for-byte reproducible packaging; timestamps/tooling metadata may differ.
- GitHub Actions cannot directly establish whether captured process traces improve instructor judgment or student learning.

## Most valuable extension: evidence quality, not event volume

The paper's natural next experiment is to test whether more process telemetry actually produces better review decisions. A stronger L4 would compare three evidence policies on the same debugging sessions:

1. **final patch + tests only**;
2. **DebugTracker compact trace**;
3. **high-volume trace** (e.g. richer editor/debugger telemetry).

Measure reviewer time, inter-rater agreement, correctness of rubric labels, evidence precision/recall against a manually annotated debugging narrative, and privacy cost (bytes/sensitive fields retained). This directly tests the central design choice: whether a small event schema is a better assessment substrate than either final-state-only grading or intrusive full capture.

A second systems-oriented extension is **tamper-evident traces**: hash-chain the JSONL event stream and compare the cost/robustness of append-only storage versus signed event batches. That would turn the current process-evidence format into stronger provenance suitable for graded or research settings.

# Scitix — scalable constraint-based type inference with missing types

Paper: **Scitix: Scalable Constraint-Based Type Inference for Code Snippets with Missing Types**  
Authors: Yiwen Dong, Zhenyang Xu, Yongqiang Tian, Edward Lee, Ondřej Lhoták, Chengnian Sun  
Venue: ISSTA 2026  
Publication page: https://conf.researchr.org/details/issta-2026/issta-2026-research-papers/33/Scitix-Scalable-Constraint-Based-Type-Inference-for-Code-Snippets-with-Missing-Types  
Official code/replication link surfaced by the authors' publication page: https://figshare.com/s/4d14f40c988bc7c55816  
Earlier thesis replication link: https://figshare.com/s/f03c5103e2ab02125b83

## Status

**Current reproduction level: scoped L2 mechanism model + L0 artifact probe.**

This directory does **not** claim an L1/L3 reproduction of the paper's F1 scores or runtime. The deterministic experiment freshly reruns the two central mechanisms on a self-contained model of the paper's motivating `Intent` example. CI also probes the official Figshare package so that artifact availability is recorded separately from experimental evidence.

## Core insight

SnR treats inference as a conventional constraint-satisfaction problem: every type variable must map to something in the knowledge base and all extracted constraints must be satisfiable. That becomes pathological when a snippet contains user-defined or otherwise missing types. One missing type can make the whole constraint set unsatisfiable, and searching subsets gets increasingly expensive as the knowledge base grows.

Scitix changes the failure model rather than simply making the solver faster:

1. **Known-missing types become `Any`.** If a simple name/method cannot be matched in the knowledge base, Scitix can explicitly represent the type as unknown instead of forcing an impossible concrete assignment.
2. **Supertype constraints are activated incrementally.** Scitix initially solves an easier satisfiable subset, then adds supertype constraints one at a time and retains only those that preserve satisfiability.
3. **Prefer information-rich solutions.** The final ranking prioritizes fewer `Any` assignments before other heuristics such as fewer libraries.

The important research idea is therefore *partial, satisfiability-preserving inference*: an unsatisfied relation involving missing context should not destroy useful evidence elsewhere in the snippet.

## Paper claims

The accepted ISSTA 2026 abstract reports:

- F1 **94.8%** on Stack Overflow snippets with a knowledge base of more than 3,000 jars;
- F1 **86.8%** on generated snippets;
- SnR times out with the large knowledge base and has F1 near zero;
- with the smallest knowledge base, Scitix reduces errors by **77%** and **45%** relative to SnR;
- compared with GPT-4o / ZS4C-class LLM baselines, Scitix reduces error rates by as much as **78%**.

### Snapshot drift worth recording

Yiwen Dong's 2025 thesis contains the pre-camera-ready Scitix study and reports different headline values:

| Metric | 2025 thesis | ISSTA 2026 abstract | change |
|---|---:|---:|---:|
| Stack Overflow F1 | 96.6% | 94.8% | -1.8 pp |
| ThaliaType/generated F1 | 88.7% | 86.8% | -1.9 pp |
| SnR error reduction, Stack Overflow | 79% | 77% | -2 pp |
| SnR error reduction, ThaliaType | 37% | 45% | +8 pp |
| max LLM error reduction | 78% | 78% | 0 pp |

`claim_audit.py` records this explicitly. Any future L1/L3 reproduction must pin the exact camera-ready artifact/dataset rather than mixing thesis tables with final-paper claims.

## What we actually rerun

`mini_scitix.py` reproduces the logical structure of the paper's motivating example:

```text
new Intent(this, Notification_morning.class)
```

The complete constraint set contains a `Main`/context type absent from the knowledge base. A strict SnR-like model is therefore UNSAT even when the correct Android `Intent` exists.

Our Scitix-like model then:

1. treats the directly missing context as `Any`;
2. temporarily removes both supertype constraints;
3. tries to add the unknown-dependent supertype relation — it makes the set unsatisfiable, so it is discarded;
4. adds the independent `java.lang.Class` relation — it remains satisfiable, so it is retained;
5. the remaining evidence selects `android.content.Intent` over competing same-simple-name candidates.

The smoke test repeats this with 0, 10, 100, 1,000 and 10,000 irrelevant same-name candidates. The purpose is **not** to claim paper-equivalent scalability; it verifies that the mechanism remains logically stable as ambiguity grows.

## Run

```bash
bash papers/2026-scitix/reproduce.sh
```

Outputs:

- `results/mechanism.json` — fresh mechanism-level run;
- `results/claim_drift.json` — thesis vs ISSTA claim audit;
- `results/artifact_probe.json` — reachability/metadata probe for both Figshare links;
- `results/summary.json` — compact CI summary.

For an offline deterministic run:

```bash
SKIP_NETWORK=1 bash papers/2026-scitix/reproduce.sh
```

## Paper vs reproduction

| Question | Paper | This reproduction |
|---|---|---|
| Can missing types poison the full CSP? | Yes; motivating example and large-KB experiments | Yes, strict model becomes UNSAT |
| Does `Any` preserve useful inference? | Yes | Yes, missing context no longer kills the candidate set |
| Can incremental supertype constraints recover precision? | Yes | Yes, `Class` relation selects Android `Intent`; unknown-dependent relation is skipped |
| >3,000-jar scalability | evaluated | **not reproduced** |
| StatType-SO / ThaliaType F1 | evaluated | **not reproduced** |
| SnR / LLM baselines | evaluated | **not reproduced** |
| Official artifact | supplied via Figshare | availability probed in CI; full execution pending artifact inspection |

## What is required for L1 / L3

### L1 — reported-results

1. retrieve and pin the final Figshare package by checksum;
2. identify the camera-ready result files and exact dataset snapshot;
3. rerun the authors' aggregation scripts without re-running inference;
4. verify the accepted 94.8% / 86.8% headline values and all RQ tables.

### L3 — paper-scale live run

Likely requirements from the thesis implementation description:

- Java implementation of Scitix/SnR;
- MariaDB knowledge base;
- StatType-SO and ThaliaType datasets;
- knowledge bases Γ0, Γ500, Γ1000, Γ1500, Γ2000, Γ2500, Γ3000 built from Maven jars;
- per-snippet timeout matching the paper;
- SnR, Scitix variants and LLM baselines using version-pinned models/prompts.

The artifact probe is deliberately separate because simply downloading the package is L0, not experimental reproduction.

## Experimental design review

The strongest aspect of the paper is that it evaluates **knowledge-base scaling** rather than only accuracy at one convenient size. This directly tests the proposed failure mode: unknown types become more expensive for a strict solver as ambiguity grows.

The ablations are also well aligned with the design. The thesis reports variants for simplified constraint addition, random ordering, package filtering and naive selection. This helps distinguish three sources of gain: tolerating missing types, the order/strategy of adding constraints, and final solution ranking.

A key reproducibility concern is snapshot drift. The thesis and final ISSTA abstract changed multiple headline numbers. That makes dataset/artifact version pinning part of the scientific result, not merely repository hygiene.

## Extensions worth doing

### 1. Information-gain constraint scheduling — highest priority

The iterative stage currently asks whether a constraint preserves satisfiability. A stronger scheduler could choose the next constraint by:

```text
expected candidate reduction / estimated solver cost
```

Compare:

- paper ordering;
- random ordering;
- cheapest-first;
- maximum candidate-elimination first;
- an online bandit/learned policy.

Metrics: F1, total solver calls, p50/p95 latency, number of retained/rejected constraints, and candidate-set entropy after each iteration. This tests whether Scitix's real reusable abstraction is not `Any` alone but **budgeted constraint activation**.

### 2. Temporal generalization / leakage-resistant evaluation

ThaliaType was designed to mitigate LLM benchmark leakage. Repeat the comparison with snippets and Maven packages released *after* the evaluated model/tool snapshots. This separates semantic inference from memorized FQNs and also tests whether Scitix degrades gracefully under ecosystem drift.

### 3. Unknown-type severity curve

Inject controlled missing context into otherwise compilable snippets: 0%, 10%, 25%, 50%, 75% of relevant types removed from the knowledge base. Plot accuracy and runtime as a function of unknown-type density. This would characterize the regime where `Any` changes from a robust escape hatch into excessive loss of information.

### 4. Compiler-toolchain analogy

The same pattern can be tested in compiler tooling: when an IR fragment contains an opaque/custom dialect op, do not fail global inference immediately. Model the unsupported portion as an opaque/`Any` node and progressively activate shape/type/layout constraints that remain satisfiable. A small MLIR/Triton prototype could measure how much useful type/layout inference survives incomplete dialect knowledge.

## Threats and limits of today's evidence

- `mini_scitix.py` is an independent mechanism model, not author code.
- It does not parse Java or use Datalog/MariaDB.
- The synthetic competing `Intent` signature is only a stand-in for same-simple-name ambiguity; no claim is made about the exact Redis API signature.
- The scale smoke test measures logical stability, not solver scalability.
- Final paper numbers are taken from the current ISSTA publication page; the thesis numbers are an earlier study snapshot.
- Until the final Figshare package is pinned and executed, the project remains below L1 for reported paper tables.

## Sources

- ISSTA 2026 paper page: https://conf.researchr.org/details/issta-2026/issta-2026-research-papers/33/Scitix-Scalable-Constraint-Based-Type-Inference-for-Code-Snippets-with-Missing-Types
- Yongqiang Tian publication list: https://yqtian.com/pub.html
- Yiwen Dong PhD thesis (Chapter 5 contains the detailed Scitix design and earlier evaluation snapshot): https://yiwendong.com/assets/pdf/Dong_Yiwen.pdf
- Chengnian Sun publication page / final replication link: https://cs.uwaterloo.ca/~cnsun/public/publication/issta26-a/

# VIZDETOUR — Detecting Rendering Bugs via Equivalent Mutations

Paper: **Detecting Rendering Bugs in Imperative Data Visualization Libraries via Equivalent Mutations** — Weiqi Lu, Yongqiang Tian, arXiv:2607.12363v3 (2026-07-16).

Paper: https://arxiv.org/abs/2607.12363

Artifact candidate: https://github.com/smith2936/vizdetour (pinned in CI to `d2b22e33b94eaff06b2116f31ddeea21bb0e6b91`). The repository describes itself as the VIZDETOUR artifact and contains workflows, seeds, and the bug dataset, but the arXiv v3 text does not link this repository directly, so provenance is recorded as plausible rather than independently anchored by the paper.

## Core insight

Imperative visualization libraries are state machines. Instead of predicting the correct pixels for an arbitrary plot, VIZDETOUR creates an **endpoint-preserving mutation**: traverse a different sequence of API updates but return to a semantically equivalent terminal state. A correct implementation should therefore render the same image. A residual difference becomes a relative oracle for silent rendering bugs.

The paper implements three operators:

1. **Set-Revert** — change a property and restore it.
2. **Redundant-Set** — assign the current value again.
3. **Remove-Readd** — remove an element and reinsert it.

Rendered images are compared with perceptual hashing. The paper calibrates the anomaly threshold at `tau = 2`; distances above 2 are suspicious.

## Paper claims

- Subjects: matplotlib 3.10.8, bokeh 3.10.0, plotly 6.8.0.
- Seed corpus: 2,487 examples (934 matplotlib, 471 bokeh, 1,082 plotly).
- Budget: 120 hours per library, 10 mutation rounds per seed.
- New bugs: 47 reported, 39 confirmed, 18 fixed.
- Confirmed symptoms: 34 incorrect plots and 5 crashes.
- Ablation: removing Set-Revert drops new bugs by 70.2%; removing Redundant-Set or Remove-Readd drops them by 14.9% each.
- Oracle calibration: 38,158 null mutations, with 38,096 at pHash distance 0 and 53 at distance 2; structural anomalies appear at distance >= 4.

## Reproduction level

**L1 + scoped L2.**

- **L1 artifact audit:** clone the pinned artifact candidate and recompute Table-I-style bug counts from `dataviz-bugs-detected.csv`. Stable claims (`reported`, `confirmed`, `fixed`) are asserted in CI. PR/fix lifecycle fields are reported but not hard-failed because they can drift after publication.
- **L2 live-minimal:** independently recreate one paper-style endpoint-preserving mutation for matplotlib issue #31257 and run the visual oracle on the paper-era matplotlib 3.10.8. The same case is also replayed on current stable matplotlib 3.11.1 to measure version drift.

This is **not** L3: we do not run all 2,487 seeds for 120 hours per library.

## Live case: matplotlib #31257

The upstream issue reports that updating a marker's `fillstyle` reconstructs its `MarkerStyle` and can drop a previously attached rotation transform. The live test creates rotated arrow markers, then applies:

```text
set_fillstyle("left") -> set_fillstyle(original)
```

The terminal fillstyle should match the seed, so the final render should also match. A pHash distance greater than the paper threshold (`2`) is treated as a detected visual anomaly.

## Paper vs our experiment

| Question | Paper | This reproduction |
|---|---|---|
| Relative oracle | pHash distance after endpoint-preserving mutation | same principle, small standalone pHash implementation |
| Main subject | 3 DataViz libraries | matplotlib only for live L2 |
| Scale | 2,487 seeds, 120 h/library | one confirmed bug case |
| Artifact evidence | Table I + bug dataset | recompute dataset counts from pinned artifact candidate |
| Version | matplotlib 3.10.8 | 3.10.8 + 3.11.1 drift lane |
| Human triage | all emitted reproducers | none; known upstream issue is used as ground truth |

## Threats / limitations

- Our pHash is a compact standard DCT implementation, not guaranteed byte-for-byte identical to the authors' implementation.
- Font rasterization and FreeType changes can affect visual hashes across runners.
- One known bug validates the mechanism but not the paper's discovery power.
- The artifact repository is not directly linked from arXiv v3; we pin the exact commit and explicitly record this provenance caveat.
- Full evaluation needs Firefox/geckodriver/Playwright plus long fuzzing campaigns for Bokeh and Plotly.

## Extension ideas

### 1. Version-drift matrix

Replay every confirmed reproducer across `paper-version -> latest stable -> main/nightly` and classify each bug as `survives`, `fixed`, or `regressed`. This converts a one-shot bug study into a longitudinal reliability dataset.

### 2. Learned invertibility oracle

The paper uses hardcoded blacklists for non-invertible API combinations. Replace this with source-aware contract inference: infer getter/setter side effects and coupled state, then predict whether a mutation is truly endpoint-preserving before execution. Measure false-positive reduction without reducing bug yield.

### 3. Stronger visual oracles

Compare pHash against SSIM, LPIPS, and structure-aware plot metadata. Report ROC-like tradeoffs using developer-confirmed bugs plus null mutations instead of choosing a single threshold.

### 4. Compiler analogy

Apply the same idea to compiler pipelines: construct pass sequences or flag perturbations that should return to an equivalent IR/program state, then use Alive2, executable equivalence, or object-code metrics as the endpoint oracle. This is the closest bridge from VIZDETOUR back to compiler testing.

## Run

```bash
./papers/2026-vizdetour/reproduce.sh
```

CI: `.github/workflows/paper-vizdetour.yml`.

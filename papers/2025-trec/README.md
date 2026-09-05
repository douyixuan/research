# T-Rec — Fine-Grained Language-Agnostic Program Reduction Guided by Lexical Syntax

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Jiarui Zhang, Puzhuo Liu, Yu Jiang, Chengnian Sun. **T-Rec: Fine-Grained Language-Agnostic Program Reduction Guided by Lexical Syntax**, ACM TOSEM 34(2), Article 34, 2025.

Paper: https://cs.uwaterloo.ca/~cnsun/public/publication/tosem24-trec/tosem24-trec.pdf

Official code: https://github.com/uw-pluverse/perses

Fresh-run pin: Perses **v2.7** (released 2026-08-26), `perses_deploy.jar` SHA-256 `1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427`.

Current level: **L0 implementation/provenance audit + scoped L2 direct T-Rec mechanism + v2.7 pipeline-drift probe**. This is **not L1 or L3**: paper-scale raw result tables are not reprocessed and the original benchmark suite is not rerun.

## Core insight

Most language-agnostic reducers treat lexer tokens as indivisible atoms. T-Rec uses the language's **lexical syntax** to reduce and canonicalize *inside* tokens. The current Perses implementation supports consistent identifier replacement, lexer-ATN-guided canonicalization of non-identifiers, fragment deletion and character-level reduction.

This attacks a local minimum that syntax-tree deletion alone cannot reach: an identifier/literal may need to remain for the property to hold, while the token itself can still be simplified.

## Paper claims used as reference, not reproduced claims

The paper evaluates canonicalization on **3,796** bug-triggering C tests representing **46** GCC 4.3.0 bugs, and reports that T-Rec enables Perses/Vulcan to eliminate **1,294 / 1,315** additional duplicates. On the multi-language benchmark it reports T-Rec-Perses byte reductions of **65.52% C / 28.34% Rust / 42.86% SMT-LIBv2**, and T-Rec-Vulcan reductions of **53.73% / 19.79% / 16.24%**.

These are context only; none are labeled reproduced here.

## Fresh scoped-L2 experiment

Input:

```c
int ExtremelyLongIdentifierForTRecDemo = 7;
int main(void) {
  return ExtremelyLongIdentifierForTRecDemo;
}
```

The deterministic property oracle recompiles each candidate using `gcc -std=c11 -O0` and accepts it only if the executable still exits with code `7`.

`reproduce.sh` verifies the official v2.7 JAR digest and runs three cases, with Vulcan, Latra, SFC and LPR explicitly disabled:

1. `direct_trec`: run the registered `token_canonicalizer` reducer directly;
2. `modern_off`: current v2.7 default pipeline with `--enable-trec false`;
3. `modern_on`: current v2.7 default pipeline with `--enable-trec true`.

Fresh GitHub Actions result:

| Probe | Bytes | Long identifier remains? | Oracle |
|---|---:|---|---|
| Original | 109 | yes | n/a |
| Direct `token_canonicalizer` | 109 | **no** | pass |
| v2.7 default, T-Rec off | 109 | **yes** | pass |
| v2.7 default, T-Rec on | 109 | **no** | pass |

The direct reducer therefore performs the intended lexical transformation end to end while preserving the property. The whole-file byte count stays at 109 because `ORIG_FORMAT` formatting compensates for the shorter lexeme; byte count on this tiny case is not a useful efficacy metric.

The modern pipeline probe is more informative: T-Rec on/off has **0-byte marginal delta** on this case, yet only the T-Rec-on result canonicalizes the required long identifier. This is evidence for mechanism behavior, not evidence for the paper's aggregate size claims.

Run locally:

```bash
bash papers/2025-trec/reproduce.sh
```

Evidence is written to `papers/2025-trec/results/`: three reduced programs, reducer logs, and `l2-summary.json`.

## Paper vs reproduction

| Question | Paper | This run |
|---|---|---|
| Scale | 3,796 canonicalization cases + multilingual suites | 1 synthetic C case |
| Reducer era | paper-era Perses/T-Rec | official Perses v2.7 |
| Result | duplicate elimination, bytes/tokens, runtime | lexical canonicalization + property preservation + current-pipeline drift |
| Baselines | Perses / Vulcan / C-Reduce variants | direct T-Rec plus current default pipeline on/off |
| Level | paper experiment | scoped **L2**, not L1/L3 |

No numerical comparison should be made between this single case and the paper's aggregate percentages.

## L0 implementation and reproducibility audit

The current source registers T-Rec's `TokenCanonicalizer` as the reducer name `token_canonicalizer`. For identifiers it tries both a single occurrence and **all lexer nodes with the same lexeme**; canonical identifier pools begin with short names such as `a`, `b`, ... .

Two important v2.7 drift findings emerged while making CI real:

- `--alg perses` is rejected by the packaged v2.7 JAR.
- the legacy `perses_node_priority_with_dfs_delta` name still appears in current benchmark scripts, but the packaged v2.7 JAR also rejects it.
- v2.7 reports **Latra enabled by default**, so a naive `--enable-trec false` run is not a clean T-Rec-off baseline. This reproduction explicitly disables Latra and the other auxiliary transformers.

These CLI/default changes are themselves reproducibility hazards for old reduction papers.

## Threats and limitations

1. **Version drift:** v2.7 is a 2026 implementation, not the exact paper-era build.
2. **Synthetic input:** scoped L2 proves a mechanism, not effectiveness on real compiler bugs.
3. **Modern toolchain:** GitHub-hosted GCC/JDK versions differ from the paper environment and GCC 4.3.0 used in the duplicate study.
4. **No L1 claim:** aggregate paper numbers were not recomputed from paper-era raw outputs.
5. **No L3 claim:** the 3,796-case study and C/Rust/SMT-LIBv2 suites were not rerun.
6. **Formatting confounder:** whole-file bytes can mask lexical shortening on tiny examples.
7. **Current default-pipeline confounder:** v2.7 has accumulated reducers/default changes, so it cannot be treated as paper-era Perses without pinning the historical implementation.

## Upgrade path

### To L1

Locate a paper-specific archive with exact per-case outputs and recompute duplicate counts, byte/token tables and runtime aggregates. The current Perses tree exposes benchmark subjects and T-Rec code, but this audit did not find a clearly labeled paper-era `Benchmark-Multi`/T-Rec result package.

### To L3

Pin the paper-era Perses/T-Rec commit, compiler/solver versions and benchmark revisions, then rerun the C/Rust/SMT-LIBv2 suite and the canonicalization study. Old vulnerable compilers, benchmark provenance and runtime cost are first-class dependencies.

## Most valuable L4 extension — lexical-transformation ROI under toolchain drift

Run paper-era bugs plus **post-paper compiler bugs** under an equal property-oracle-call budget and compare:

- historical Perses only;
- historical Perses + T-Rec;
- current v2.7 pipeline with T-Rec off/on;
- identifier-only canonicalization;
- literal/ATN canonicalization only;
- fragment/character deletion only;
- Vulcan / SFC / Latra / DRReduce as modern baselines.

Record accepted transformations, lexeme/token/byte savings, oracle calls, wall time and duplicate-collapse rate. Repeat across a paper-era commit and v2.7. This directly separates **T-Rec transformation value** from reducer/toolchain drift.

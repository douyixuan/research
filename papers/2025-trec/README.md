# T-Rec — Fine-Grained Language-Agnostic Program Reduction Guided by Lexical Syntax

Paper: Zhenyang Xu, Yongqiang Tian, Mengxiao Zhang, Jiarui Zhang, Puzhuo Liu, Yu Jiang, Chengnian Sun. **T-Rec: Fine-Grained Language-Agnostic Program Reduction Guided by Lexical Syntax**, ACM TOSEM 34(2), Article 34, 2025.

Paper: https://cs.uwaterloo.ca/~cnsun/public/publication/tosem24-trec/tosem24-trec.pdf

Official code: https://github.com/uw-pluverse/perses

Fresh-run pin: Perses **v2.7** (released 2026-08-26), `perses_deploy.jar` SHA-256 `1102ec7e3e601792a3c271c41ac7df52b03fca635df552500c241933c2c1e427`.

Current level: **L0 implementation/provenance audit + scoped L2 current-release mechanism probe** once the included CI lane passes. This is **not L1 or L3**: the paper-scale raw result tables are not reprocessed here, and the original benchmark suite is not rerun at paper scale.

## Core insight

Most language-agnostic reducers treat lexer tokens as indivisible atoms. T-Rec uses the language's **lexical syntax** to reduce and canonicalize *inside* tokens. Its current Perses implementation handles:

- identifier canonicalization, including consistent replacement of all occurrences of a lexeme;
- lexer-ATN-guided canonical replacement of non-identifier tokens;
- deletion of lexer fragments when the property still holds;
- character-level canonicalization.

This attacks a local minimum that syntax-tree deletion alone cannot reach: a program may require an identifier/literal token to remain, yet the token itself can still be made much shorter.

## Paper claims used as reference, not reproduced claims

The paper evaluates canonicalization on **3,796** bug-triggering C tests representing **46** GCC 4.3.0 bugs, and reports that T-Rec enables Perses/Vulcan to eliminate **1,294 / 1,315** additional duplicates. On the multi-language reduction benchmark it reports maximum average byte-size improvements of **65.52%** over Perses and **53.73%** over Vulcan for C.

For the three multi-language groups, the paper reports T-Rec-Perses byte reductions of approximately **65.52% C / 28.34% Rust / 42.86% SMT-LIBv2**, and T-Rec-Vulcan reductions of **53.73% / 19.79% / 16.24%**. These are context only; this directory does not label them as reproduced.

## What this reproduction actually runs

`reproduce.sh` downloads the current official Perses v2.7 release JAR, verifies its SHA-256, and runs the same tiny C program twice with a deterministic oracle:

1. **baseline:** Perses with `--enable-trec false`, Vulcan disabled;
2. **T-Rec:** the same Perses release/configuration with `--enable-trec true`.

Input:

```c
int ExtremelyLongIdentifierForTRecDemo = 7;
int main(void) {
  return ExtremelyLongIdentifierForTRecDemo;
}
```

The property oracle recompiles each candidate with GCC and accepts it only when the executable still exits with code `7`. The declaration and use therefore cannot simply disappear. Plain syntax deletion has no rename operation; T-Rec can canonicalize the required identifier while preserving the property.

The run asserts all of the following:

- baseline reduced output still satisfies the oracle;
- T-Rec reduced output still satisfies the oracle;
- the long identifier disappears from the T-Rec result;
- the T-Rec result is smaller in bytes than the no-T-Rec baseline.

Run locally:

```bash
bash papers/2025-trec/reproduce.sh
```

Evidence is written to `papers/2025-trec/results/`: `baseline.c`, `trec.c`, both reducer logs, and `l2-summary.json`.

## Paper vs reproduction

| Question | Paper | This run |
|---|---|---|
| Main scale | 3,796 canonicalization cases + multilingual reduction suites | 1 synthetic C case |
| Reducer era | paper-era Perses/T-Rec | official Perses v2.7 (2026-08-26) |
| Main result | aggregate duplicate elimination, bytes/tokens, runtime | mechanism-level byte delta and oracle preservation |
| Baseline | Perses / Vulcan / C-Reduce variants | same v2.7 Perses, T-Rec toggled off |
| Level justified | paper experiment | scoped **L2** only after fresh CI success |

No numerical comparison should be made between this one-case byte delta and the paper's 65.52% C aggregate: they answer different questions at radically different scales.

## L0 implementation audit

The current official Perses source keeps T-Rec as `TokenCanonicalizer`. The implementation iterates lexer tokens and, for identifiers, tries both replacing a single occurrence and replacing **all lexer nodes with the same lexeme**. Canonical identifier pools start with short names (`a`, `b`, ... and a separate uppercase pool), while other token classes use lexer-ATN-derived candidates plus fragment/character reduction.

The current command-line flag remains `--enable-trec` and defaults to `true`; Vulcan defaults to `false`. This makes a same-binary toggle experiment a cleaner baseline than comparing separate builds.

## Threats and limitations

1. **Version drift:** v2.7 is a 2026 implementation, not necessarily the exact commit used for the 2024/2025 paper evaluation.
2. **Synthetic input:** the scoped L2 case proves the reduction mechanism, not effectiveness on real compiler bugs.
3. **Modern toolchain:** GitHub-hosted GCC/JDK versions differ substantially from the paper environment and from GCC 4.3.0 used in its duplicate study.
4. **No L1 claim:** the published aggregate numbers are not recomputed from paper-era raw outputs in this directory.
5. **No L3 claim:** the 3,796-case canonicalization benchmark and multilingual reduction suites are not rerun.
6. **Metric scope:** bytes on a single tiny program are highly sensitive to formatting and cannot estimate population-level effectiveness.

## Blockers / upgrade path

### To L1

Locate a paper-specific release of the exact per-case result outputs (or an archived paper artifact) and recompute the duplicate counts, byte/token tables and runtime aggregates from those raw files. The current Perses repository contains benchmark subjects and T-Rec code, but this audit did not find a clearly labeled `Benchmark-Multi`/T-Rec result package by those paper names.

### To L3

Pin the paper-era Perses/T-Rec commit, compilers/solvers and benchmark revisions, then rerun the full C/Rust/SMT-LIBv2 suite and the canonicalization study. Old vulnerable compilers, benchmark provenance and runtime cost become first-class reproducibility dependencies.

## Most valuable L4 extension — lexical-transformation ROI under toolchain drift

Run paper-era bugs plus **post-paper compiler bugs** under an equal property-oracle-call budget and compare:

- Perses only;
- Perses + full T-Rec;
- identifier-only canonicalization;
- literal/ATN canonicalization only;
- fragment/character deletion only;
- Vulcan / SFC / Latra / DRReduce as modern reduction baselines.

Record accepted transformations, downstream byte/token savings, oracle calls, wall time and duplicate-collapse rate. Repeat on a paper-era Perses commit and current v2.7. This separates **T-Rec's actual transformation value** from improvements or regressions caused by reducer/toolchain drift.

A second useful ablation is canonicalization collision behavior: classify cases where aggressive identifier merging improves duplicate detection, where it is rejected by the oracle, and where language semantics make case-sensitive pools or token-level replacement insufficient.

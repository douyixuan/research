# Ad Hoc Syntax-Guided Program Reduction

Tian, Zhang, Xu, Tian, Dong, Sun. **Ad Hoc Syntax-Guided Program Reduction.** ESEC/FSE 2023 Demonstrations. DOI: `10.1145/3611643.3613101`.

## Core insight

Perses is algorithmically language-agnostic, but historically adding a language still required manual grammar normalization, source integration and a rebuild. `Perses^adhoc` turns that integration step into data: provide an ANTLR grammar plus a small YAML language description, run the ad-hoc installer to generate a language-support JAR, then pass that JAR to the unchanged Perses reducer.

The paper reports that the GLSL support burden drops from about **190 lines** of Perses infrastructure to about **20 lines** of configuration, while ad-hoc reduction remains comparable in effectiveness/efficiency to built-in Perses. Public descriptions disagree slightly on the quoted installation time (roughly 10 vs 20 seconds), so this repository treats that number as a paper-side claim rather than a reproduced constant.

## Reproduction level

**L0 artifact/source audit + official current-source scoped L2.**

- L0: verified that current public Perses still contains the official ad-hoc installer, documentation, language-extension interface and system-test path.
- L2: CI builds the official current Perses source at a pinned commit, generates support for a new repository-local `Tiny` grammar, and runs the official reducer end to end against a deterministic property oracle.
- **Not L1:** the paper's historical result tables are not recomputed from released result artifacts.
- **Not L3:** the full 2023 benchmark suite and paper-era toolchain are not rerun.

## Run

```bash
bash papers/2023-adhoc-perses/reproduce.sh
```

Requirements: Linux, Git, Java/JDK as required by the pinned Perses source, Go (used to install Bazelisk), and network access to clone the official Perses repository and Bazel dependencies. GitHub Actions executes the same entrypoint.

The run writes evidence to `papers/2023-adhoc-perses/results/official/`, including build/install/reduction logs, `metrics.json`, the reduced program, environment information, and a SHA-256 checksum for the generated language JAR.

## Fresh L2 case

The new Tiny language contains `let` and `bug` statements. The input has four statements; the property oracle only requires the bug marker and its identifier to survive. The workflow:

1. builds `perses_adhoc_installer_deploy.jar` and `perses_deploy.jar` from pinned official source;
2. converts `Tiny.g4` + `language_kind.yaml` into `tiny-language.jar`;
3. supplies that JAR through `--language-ext-jars` without adding Tiny-specific code to Perses;
4. runs syntax-guided reduction;
5. asserts that the output is smaller and still contains `bug` and `keep`.

See [`experiment.md`](experiment.md) for the design, threats, promotion path and proposed L4 extension.

## Sources

- Paper/Monash record: https://research.monash.edu/en/publications/ad-hoc-syntax-guided-program-reduction/
- FSE 2023 demo page: https://2023.esec-fse.org/details/fse-2023-demonstrations/12/Ad-Hoc-Syntax-Guided-Program-Reduction
- Official Perses repository: https://github.com/uw-pluverse/perses
- Current install-new-language documentation: https://github.com/uw-pluverse/perses/blob/master/doc/install_new_languages.md

## Result status

The CI-produced numeric result is recorded in `results/official/metrics.json` in the uploaded workflow artifact. This README is updated after CI so that only actually observed values are reported here.

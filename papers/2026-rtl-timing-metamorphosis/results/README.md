# Verified CI result

Source run: https://github.com/douyixuan/research/actions/runs/33344310686

The first GitHub Actions execution completed successfully on 2026-08-31 and uploaded `rtl-timing-metamorphosis-results`.

Fresh scoped-L2 measurements:

- Icarus Verilog exhaustive equivalence: **8/8 input vectors passed**.
- Yosys formal equivalence: **passed** (`equiv_status -assert`).
- Toolchain: **Yosys 0.33** (`2584903a060`), **Icarus Verilog 12.0 stable**.
- Current-Yosys structural proxy after synthesis:
  - original: **3 cells, 6 netnames, 6 wire bits**;
  - mutant: **5 cells, 8 netnames, 8 wire bits**;
  - mutant/original: **1.6667× cells, 1.3333× netnames, 1.3333× wire bits**.

These ratios are **not** the paper's 153-case PPA results. They are a fresh one-case modern-toolchain probe. In particular, the paper's public v1 reports a Yosys logic-operation aggregate of 4.67× wires and 3.25× cells; this run is too small and uses a different/current toolchain and metric proxy, so the numerical difference is expected and must not be treated as a contradiction.

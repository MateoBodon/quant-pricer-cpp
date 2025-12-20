---
generated_at: 2025-12-20T21:11:15Z
git_sha: 36c52c1d72dbcaacd674729ea9ab4719b3fd6408
branch: master
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - rg --files
  - rg --files -g '*.py'
  - python3 tools/project_state_generate.py
  - uname -a
  - cmake --version
---

# Dataflow

## Core pricing dataflow (C++)
- Inputs: spot, strike, rate, dividend, volatility, tenor; optional schedules (`quant::PiecewiseConstant`).
- Engines:
  - Black–Scholes analytics (`include/quant/black_scholes.hpp`).
  - Monte Carlo GBM/QMC (`include/quant/mc.hpp`, `include/quant/qmc/*`).
  - PDE Crank–Nicolson (`include/quant/pde.hpp`).
  - American/Barrier/Exotic/Heston/risk modules in corresponding headers.
- Outputs: prices, Greeks, and diagnostic stats (MC standard errors, CI bands, PDE theta).

## CLI dataflow
- CLI parses args → constructs params → calls core library → prints scalar or JSON result.
- JSON output is used by tests and artifact scripts for reproducibility.

## Artifact dataflow (scripts → docs/artifacts)
- Scripts in `scripts/` call `quant_cli` or library entrypoints and emit CSV/PNG artifacts.
- `scripts/manifest_utils.py` updates `docs/artifacts/manifest.json` with git/system metadata.
- `scripts/generate_metrics_summary.py` reads artifacts and writes `docs/artifacts/metrics_summary.md/json`.

## WRDS pipeline dataflow
- Ingest: `wrds_pipeline/ingest_sppx_surface.py` loads WRDS/IvyDB (or sample bundle) and filters by DTE/moneyness.
- Calibration: `wrds_pipeline/calibrate_heston.py` (and BS baseline in `calibrate_bs.py`).
- OOS pricing: `wrds_pipeline/oos_pricing.py` computes next-day errors.
- Δ-hedged PnL: `wrds_pipeline/delta_hedge_pnl.py`.
- Aggregation + figures: `wrds_pipeline/pipeline.py` writes aggregated CSV/PNG to `docs/artifacts/wrds/` (or output root).

## Results reporting
- Narrative summaries live in `docs/Results.md`, `docs/WRDS_Results.md`, and `docs/Validation*.md`.
- Artifacts are the source of truth; summaries cite CSV/PNG paths.

---
generated_at: 2025-12-22T19:13:19Z
git_sha: 5265c6de1a7e13f4bfc8708f188986cee30b18ed
branch: feature/ticket-00_project_state_refresh
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - c++ --version
  - cmake --version
  - uname -a
  - rg --files
  - rg --files -g '*.py'
  - rg --files tests
  - rg -n "argparse|click|typer" scripts wrds_pipeline python tests tools
  - python3 tools/project_state_generate.py
---

# Dataflow

## Core pricing dataflow (C++)
- Inputs: spot, strike, rate, dividend, volatility, tenor; optional schedules (`quant::PiecewiseConstant`).
- Engines:
  - Black–Scholes analytics (`include/quant/black_scholes.hpp`).
  - Monte Carlo GBM/QMC (`include/quant/mc.hpp`, `include/quant/qmc/*`).
  - PDE Crank–Nicolson (`include/quant/pde.hpp`).
  - American/Barrier/Exotic/Heston/Risk modules in corresponding headers.
- Outputs: prices, Greeks, and diagnostics (MC standard errors, CI bands, PDE theta).

## CLI dataflow
- CLI parses args → constructs params → calls core library → prints scalar or JSON result.
- JSON output is used by tests and artifact scripts for reproducibility.

## Artifact dataflow (scripts → artifacts)
- Artifact scripts call `quant_cli` or Python helpers and emit CSV/PNG results.
- Reproducible run outputs are under `docs/artifacts/` (manifest + metrics summary are authoritative).
- Some scripts still default to `artifacts/` for local analyses (e.g., `scripts/greeks_reliability.py`, `scripts/parity_checks.py`).
- `scripts/manifest_utils.py` updates `docs/artifacts/manifest.json` with git/system metadata.
- `scripts/generate_metrics_summary.py` reads artifacts and writes `docs/artifacts/metrics_summary.md/json`.

## WRDS pipeline dataflow
- Ingest: `wrds_pipeline/ingest_sppx_surface.py` loads WRDS/IvyDB (or sample bundle) and filters by DTE/moneyness.
- Calibration: `wrds_pipeline/calibrate_heston.py` (and BS baseline in `calibrate_bs.py`).
- OOS pricing: `wrds_pipeline/oos_pricing.py` computes next-day errors.
- Δ-hedged PnL: `wrds_pipeline/delta_hedge_pnl.py`.
- Aggregation + figures: `wrds_pipeline/pipeline.py` writes aggregated CSV/PNG to `docs/artifacts/wrds/`.

## Data-policy guard
- `scripts/check_data_policy.py` scans tracked files under `artifacts/`, `docs/artifacts/`, `data/`, and `wrds_pipeline/sample_data/` for restricted patterns.
- `wrds_pipeline/sample_data/*.csv` must begin with `# SYNTHETIC_DATA`.
- Live WRDS or local OptionMetrics data must stay outside the repo or under gitignored paths.

## Results reporting
- Narrative summaries live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md`.
- Artifacts are the source of truth; summaries cite CSV/PNG paths.

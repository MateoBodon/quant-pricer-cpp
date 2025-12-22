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

# Experiments

## Core validation scripts (artifacts)
- `scripts/tri_engine_agreement.py` → `docs/artifacts/tri_engine_agreement.csv/png`.
- `scripts/qmc_vs_prng_equal_time.py` → `docs/artifacts/qmc_vs_prng_equal_time.csv/png`.
- `scripts/pde_order_slope.py` → `docs/artifacts/pde_order_slope.csv/png`.
- `scripts/mc_greeks_ci.py` → `docs/artifacts/mc_greeks_ci.csv/png`.
- `scripts/heston_qe_vs_analytic.py` → `docs/artifacts/heston_qe_vs_analytic.csv/png`.
- `scripts/ql_parity.py` → `docs/artifacts/ql_parity/ql_parity.csv/png`.

## Benchmarks
- C++ benchmarks: `benchmarks/bench_mc.cpp`, `benchmarks/bench_pde.cpp`, `benchmarks/bench_sanity.cpp`.
- Artifact post-processing: `scripts/generate_bench_artifacts.py` → `docs/artifacts/bench/`.

## WRDS experiments
- `wrds_pipeline/pipeline.py` (single date or multi-date panel) → `docs/artifacts/wrds/`.
- `wrds_pipeline/compare_bs_heston.py` → `docs/artifacts/wrds/wrds_bs_heston_comparison.csv` and plots.
- `scripts/build_wrds_cache.py` — optional local cache builder for live data (outputs outside repo by default).

## Other analytical scripts
- `scripts/greeks_reliability.py`, `scripts/greeks_variance.py` — MC Greeks diagnostics (default outputs under `artifacts/`).
- `scripts/american_consistency.py` — American pricing checks (default outputs under `artifacts/`).
- `scripts/parity_checks.py` — parity validation (default outputs under `artifacts/`).
- `scripts/risk_backtest.py` — risk module backtests.
- `scripts/multiasset_figures.py`, `scripts/sabr_slice_calibration.py` — multi-asset / SABR experiments.

## Experiment outputs outside docs/artifacts
- `artifacts/heston/` contains Heston calibration series outputs (CSV/PNG/JSON).
- Use `scripts/calibrate_heston_series.py` and `scripts/heston_series_plot.py` to regenerate.

## Notes
- No top-level `experiments/` directory exists in the repo at this time.

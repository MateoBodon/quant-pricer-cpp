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

# Module Summaries

## C++ core modules (public headers)
- `include/quant/black_scholes.hpp` — Black–Scholes analytics, Greeks, implied vol helpers.
- `include/quant/mc.hpp` — Monte Carlo pricing + Greeks with variance reduction/QMC hooks.
- `include/quant/pde.hpp` — Crank–Nicolson PDE pricing and Greeks.
- `include/quant/american.hpp` — American option engines (binomial, PSOR, LSMC).
- `include/quant/barrier.hpp`, `include/quant/bs_barrier.hpp`, `include/quant/mc_barrier.hpp`, `include/quant/pde_barrier.hpp` — barrier option analytics/MC/PDE.
- `include/quant/heston.hpp` — Heston analytic pricer and QE Monte Carlo.
- `include/quant/asian.hpp`, `include/quant/lookback.hpp`, `include/quant/digital.hpp` — exotic payoff support.
- `include/quant/risk.hpp` — VaR/CVaR and backtest utilities.
- `include/quant/multi.hpp` — multi-asset basket MC utilities.
- `include/quant/qmc/` — Sobol sequence + Brownian bridge utilities.
- `include/quant/term_structures.hpp` — piecewise-constant schedules for rate/div/vol.
- `include/quant/rng.hpp` — RNG abstraction (counter-based, MT/PCG modes).
- `include/quant/stats.hpp`, `include/quant/math.hpp`, `include/quant/grid_utils.hpp`, `include/quant/version.hpp` — shared math/stats helpers and versioning.

## Executables and bindings
- `src/main.cpp` — `quant_cli` entrypoint (multi-engine CLI).
- `python/pybind_module.cpp` — pybind11 bindings for `pyquant_pricer`.

## Python modules (AST-derived inventory)
The table below is generated from `project_state/_generated/symbol_index.json`.

| Module | Path | Functions | Classes | Tag |
| --- | --- | --- | --- | --- |
| python.examples.quickstart | `python/examples/quickstart.py` | 5 | 0 | python |
| python.scripts.cibw_smoke | `python/scripts/cibw_smoke.py` | 1 | 0 | python |
| scripts.american_consistency | `scripts/american_consistency.py` | 4 | 1 | script |
| scripts.build_wrds_cache | `scripts/build_wrds_cache.py` | 13 | 0 | script |
| scripts.calibrate_heston | `scripts/calibrate_heston.py` | 15 | 2 | script |
| scripts.calibrate_heston_series | `scripts/calibrate_heston_series.py` | 2 | 0 | script |
| scripts.check_data_policy | `scripts/check_data_policy.py` | 7 | 0 | script |
| scripts.data.cboe_csv | `scripts/data/cboe_csv.py` | 5 | 0 | script |
| scripts.data.wrds_fetch_options | `scripts/data/wrds_fetch_options.py` | 1 | 0 | script |
| scripts.data.wrds_fetch_returns | `scripts/data/wrds_fetch_returns.py` | 3 | 0 | script |
| scripts.generate_bench_artifacts | `scripts/generate_bench_artifacts.py` | 10 | 0 | script |
| scripts.generate_metrics_summary | `scripts/generate_metrics_summary.py` | 22 | 1 | script |
| scripts.generate_synthetic_data | `scripts/generate_synthetic_data.py` | 4 | 0 | script |
| scripts.gpt_bundle | `scripts/gpt_bundle.py` | 9 | 0 | script |
| scripts.greeks_reliability | `scripts/greeks_reliability.py` | 11 | 1 | script |
| scripts.greeks_variance | `scripts/greeks_variance.py` | 2 | 0 | script |
| scripts.heston_qe_vs_analytic | `scripts/heston_qe_vs_analytic.py` | 7 | 0 | script |
| scripts.heston_series_plot | `scripts/heston_series_plot.py` | 3 | 0 | script |
| scripts.manifest_utils | `scripts/manifest_utils.py` | 15 | 0 | script |
| scripts.mc_greeks_ci | `scripts/mc_greeks_ci.py` | 4 | 0 | script |
| scripts.multiasset_figures | `scripts/multiasset_figures.py` | 2 | 0 | script |
| scripts.package_validation | `scripts/package_validation.py` | 2 | 0 | script |
| scripts.parity_checks | `scripts/parity_checks.py` | 6 | 0 | script |
| scripts.pde_order_slope | `scripts/pde_order_slope.py` | 4 | 0 | script |
| scripts.ql_parity | `scripts/ql_parity.py` | 8 | 1 | script |
| scripts.qmc_vs_prng_equal_time | `scripts/qmc_vs_prng_equal_time.py` | 7 | 1 | script |
| scripts.report | `scripts/report.py` | 9 | 0 | script |
| scripts.risk_backtest | `scripts/risk_backtest.py` | 2 | 0 | script |
| scripts.sabr_slice_calibration | `scripts/sabr_slice_calibration.py` | 4 | 0 | script |
| scripts.tri_engine_agreement | `scripts/tri_engine_agreement.py` | 8 | 0 | script |
| tests.test_cli_fast | `tests/test_cli_fast.py` | 11 | 0 | test |
| tests.test_data_policy_fast | `tests/test_data_policy_fast.py` | 1 | 0 | test |
| tests.test_greeks_reliability_fast | `tests/test_greeks_reliability_fast.py` | 1 | 0 | test |
| tests.test_heston_fast | `tests/test_heston_fast.py` | 1 | 0 | test |
| tests.test_heston_safety_fast | `tests/test_heston_safety_fast.py` | 1 | 0 | test |
| tests.test_heston_series_fast | `tests/test_heston_series_fast.py` | 1 | 0 | test |
| tests.test_metrics_snapshot_fast | `tests/test_metrics_snapshot_fast.py` | 4 | 0 | test |
| tests.test_parity_fast | `tests/test_parity_fast.py` | 1 | 0 | test |
| tests.test_qmc_fast | `tests/test_qmc_fast.py` | 1 | 0 | test |
| tools.project_state_generate | `tools/project_state_generate.py` | 16 | 1 | tool |
| wrds_pipeline | `wrds_pipeline/__init__.py` | 0 | 0 | wrds_pipeline |
| wrds_pipeline.bs_utils | `wrds_pipeline/bs_utils.py` | 6 | 0 | wrds_pipeline |
| wrds_pipeline.calibrate_bs | `wrds_pipeline/calibrate_bs.py` | 5 | 1 | wrds_pipeline |
| wrds_pipeline.calibrate_heston | `wrds_pipeline/calibrate_heston.py` | 21 | 1 | wrds_pipeline |
| wrds_pipeline.compare_bs_heston | `wrds_pipeline/compare_bs_heston.py` | 13 | 0 | wrds_pipeline |
| wrds_pipeline.delta_hedge_pnl | `wrds_pipeline/delta_hedge_pnl.py` | 2 | 0 | wrds_pipeline |
| wrds_pipeline.ingest_sppx_surface | `wrds_pipeline/ingest_sppx_surface.py` | 23 | 0 | wrds_pipeline |
| wrds_pipeline.oos_pricing | `wrds_pipeline/oos_pricing.py` | 2 | 0 | wrds_pipeline |
| wrds_pipeline.pipeline | `wrds_pipeline/pipeline.py` | 11 | 0 | wrds_pipeline |
| wrds_pipeline.tests.test_wrds_pipeline | `wrds_pipeline/tests/test_wrds_pipeline.py` | 7 | 0 | wrds_pipeline |

## Notable Python modules
- `wrds_pipeline/pipeline.py` — orchestrates WRDS ingest → calibration → OOS/PnL → summary plots.
- `wrds_pipeline/calibrate_heston.py` / `wrds_pipeline/calibrate_bs.py` — model calibration utilities.
- `wrds_pipeline/compare_bs_heston.py` — summarizes BS vs Heston aggregates.
- `scripts/reproduce_all.sh` (shell) — top-level artifact reproduction pipeline (see `project_state/PIPELINE_FLOW.md`).
- `scripts/generate_metrics_summary.py` — produces `docs/artifacts/metrics_summary.md/json` from artifact outputs.
- `scripts/check_data_policy.py` — guards tracked data artifacts for restricted columns/synthetic markers.

# Module Summaries

## C++ core (`include/quant`, `src`)
- **include/quant/math.hpp / src (inline)**  
  Utilities: Acklam/Moro inverse normal CDF (`inverse_normal_cdf`), 95% z-quantile constant. Used by RNG transforms, MC, QMC, option analytics.

- **include/quant/stats.hpp**  
  Streaming Welford accumulator (`Welford::add`, `merge`, `variance`) backing MC statistics and Greeks.

- **include/quant/rng.hpp**  
  Counter-based deterministic RNG (`uniform`, `normal`) plus hash mixing; supports `rng::Mode` (Mt19937, Counter). Depends on `math.hpp`.

- **include/quant/term_structures.hpp**  
  `PiecewiseConstant` schedule with `value(t)` lookup; shared by MC and PDE for time-dependent r/q/σ.

- **include/quant/barrier.hpp**  
  Enums `OptionType`, `BarrierType`, struct `BarrierSpec{type,B,rebate}` used across BS, MC, PDE, American.

- **include/quant/black_scholes.hpp` + `src/black_scholes.cpp`**  
  Analytic BS prices/Greeks (`call_price`, `put_price`, `delta_*`, `gamma`, `vega`, `theta_*`, `rho_*`), helpers `d1/d2`, implied vol solvers `implied_vol_call/put` (Brent with bracketing, degenerate cases). Handles zero time/vol edge cases.

- **include/quant/bs_barrier.hpp` + `src/bs_barrier_rr.cpp`**  
  Reiner–Rubinstein closed-form barrier pricer `reiner_rubinstein_price(opt, barrier, S,K,r,q,σ,T)` covering up/down, in/out, rebates, zero-vol/time degeneracies.

- **include/quant/grid_utils.hpp` + `src/grid_utils.cpp`**  
  Grid builders for PDE: tanh `stretch_map`, `build_space_grid` (S or log-S), operator assembly (`assemble_operator`) producing tridiagonal coefficients, boundary helper `dirichlet_boundary`.

- **include/quant/pde.hpp` + `src/pde.cpp`**  
  Crank–Nicolson solver for European options. `GridSpec`, `PdeParams` (log-space, boundaries, Rannacher, optional schedules), `solve_tridiagonal`, `price_crank_nicolson` (interp Δ/Γ, optional Θ via backward difference).

- **include/quant/pde_barrier.hpp` + `src/pde_barrier.cpp`**  
  Log-space CN barrier pricer `price_barrier_crank_nicolson`, Greeks via interpolation `price_barrier_crank_nicolson_greeks`; uses knock-in/out parity and Brownian-grid setup respecting barrier side.

- **include/quant/mc.hpp` + `src/mc.cpp`**  
  Monte Carlo GBM engine. `McParams` (antithetic, control variate, QMC Sobol, Brownian bridge, schedules, steps, RNG mode), `McResult`/`McStatistic`. `price_european_call` (streaming, OpenMP parallel, optional schedules) and `greeks_european_call` (pathwise Δ/ν, LRM Γ, mixed Γ, Θ finite diff). Helpers for deterministic Brownian bridge mapping and Sobol.

- **include/quant/mc_barrier.hpp` + `src/mc_barrier.cpp`**  
  Barrier MC with Brownian-bridge crossing probability, handles knock-in/out, parity, rebates, control variate disabled for KIs. Shares QMC/bridge options, pathwise crossing probability formula.

- **include/quant/asian.hpp` + `src/asian.cpp`**  
  Arithmetic/Geometric Asian MC `price_mc` with optional geometric control variate, Sobol support, antithetic sampling.

- **include/quant/lookback.hpp` + `src/lookback.cpp`**  
  Lookback (fixed/floating) MC `price_mc`, optional Brownian bridge for extrema, antithetic sampling.

- **include/quant/digital.hpp` + `src/digital.cpp`**  
  Cash-or-nothing / asset-or-nothing BS prices `price_bs`.

- **include/quant/multi.hpp` + `src/multi.cpp`**  
  Multi-asset basket MC (`basket_european_call_mc` with Cholesky on corr) and Merton jump-diffusion MC (`merton_call_mc`), antithetic optional.

- **include/quant/american.hpp` + `src/american.cpp`**  
  American option suite: binomial CRR `price_binomial_crr`; PSOR finite-difference `price_psor` (omega, Rannacher, Neumann/Dirichlet, stretched grids) + bump Greeks `greeks_psor_bump`; LSMC `price_lsmc` (polynomial basis, ridge, ITM filtering, diagnostics: itm_counts, regression_counts, condition_numbers).

- **include/quant/risk.hpp` + `src/risk.cpp`**  
  VaR/CVaR utilities: historical `var_cvar_from_pnl`, GBM MC `var_cvar_gbm`, portfolio copula `var_cvar_portfolio`, Student-t `var_cvar_t`; Kupiec/Christoffersen backtests `kupiec_christoffersen`.

- **include/quant/qmc/sobol.hpp` + `src/qmc/sobol.cpp`**  
  SobolSequence (Joe–Kuo dir. numbers, up to 64 dims, optional digital shift scramble). `generate(index)` returns quasi point.

- **include/quant/qmc/brownian_bridge.hpp` + `src/qmc/brownian_bridge.cpp`**  
  BrownianBridge transforms N(0,1) sequence to time-ordered increments with precomputed weights/indexing.

- **include/quant/heston.hpp` + `src/heston.cpp`**  
  Heston analytic call (`call_analytic` via Gauss–Laguerre 32), characteristic function, implied BS vol, Andersen QE / Euler MC (`call_qe_mc` with CIR variance evolution, antithetic, counter RNG).

- **src/main.cpp**  
  CLI dispatcher `quant_cli` covering bs/iv/mc/barrier/pde/american/digital/asian/lookback/heston/risk; parses flags, optional JSON output, OpenMP thread override, CI display.

- **python/pybind_module.cpp**  
  pybind11 bindings exposing BS, MC price/Greeks, barrier (BS/MC/PDE), PDE GridSpec/PdeParams, American (binomial/PSOR/LSMC), Heston analytic/QE MC, risk enums, PiecewiseConstant schedules, enums for QMC/bridges/RNG.

## WRDS pipeline (`wrds_pipeline/`)
- **ingest_sppx_surface.py** – Fetch SPX from WRDS (if env present) or bundled sample, filter DTE ≥21d & moneyness 0.75–1.25, compute mid IV via project solver, vega, bucket by tenor/moneyness, emit aggregated surface CSV. Env: `WRDS_ENABLED`, `WRDS_USERNAME`, `WRDS_PASSWORD`.
- **calibrate_heston.py** – Heston calibration on aggregated surface: least-squares in IV space (bounded params with internal transform), apply model to add model_price/iv/errors/weights, compute in-sample metrics, bootstrap CIs, plot fit, write tables/manifest.
- **calibrate_bs.py** – BS baseline: per-tenor vega-weighted mean σ, apply to surface/OOS, compute IV/price errors and metrics.
- **oos_pricing.py** – Apply calibrated params to next-day surface, compute per-bucket IV/price MAE (vega×quote weights), emit detail/summary CSVs.
- **delta_hedge_pnl.py** – Simulate 1-day Δ-hedged PnL using BS delta from prior-day IV; outputs detail and summary (mean_ticks, σ).
- **compare_bs_heston.py** – Aggregate per-date insample/OOS/PNL from `docs/artifacts/wrds/per_date`, build comparison CSV and plots (IV RMSE bars, OOS heatmap, PnL σ).
- **pipeline.py** – Orchestrator: load surfaces for trade + next trade, run Heston + BS calibration, OOS, PnL, plots (summary, insample, OOS, hedge, multi-date heatmap), update manifest, aggregate to `wrds_agg_*.csv`; supports batch dateset YAML/JSON and `--use-sample/--fast`.
- **bs_utils.py** – Lightweight BS price/delta/vega and implied-vol solver used throughout pipeline.
- **tests/test_wrds_pipeline.py** – MARKET test: executes pipeline on two dates (if WRDS env), asserts artifact presence and metric ranges; skip with code 77 when disabled.

## Experiment / utility scripts (`scripts/`)
- **manifest_utils.py** – Shared manifest writer: captures git/system/build metadata and experiment runs into `docs/artifacts/manifest.json`.
- **calibrate_heston.py** – Standalone calibration for normalized CSV schema (`scripts/data/schema.md`); multiple parameter transforms, retries, plots CSV/PNG under `artifacts/heston`.
- **tri_engine_agreement.py, qmc_vs_prng_equal_time.py, mc_greeks_ci.py, heston_qe_vs_analytic.py, pde_order_slope.py, ql_parity.py, heston_series_plot.py, risk_backtest.py, american_consistency.py, greeks_variance.py, greeks_reliability.py, parity_checks.py, package_validation.py, generate_bench_artifacts.py, reproduce_all.sh** – Drivers that run deterministic scenarios, benchmarks, or comparisons and emit CSV/PNG + manifest entries (see PIPELINE_FLOW/EXPERIMENTS for details).

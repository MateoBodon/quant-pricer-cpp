# Pipeline Flow

## Core CLI (`quant_cli`)
- **Command:** `build/quant_cli <engine> ...` (bs, iv, mc, barrier bs|mc|pde, pde, american binomial|psor|lsmc, digital, asian, lookback, heston, risk).
- **Flow:** Parse args → build parameter struct → call corresponding C++ engine → print scalar or JSON (optionally with CIs/Greeks) → exit.
- **Inputs:** Scalar market params; MC engines accept paths/seed/QMC/bridge/steps; PDE accepts grid spec.
- **Outputs:** Price/Greeks/metrics on stdout (CI bounds for MC & Heston MC).

## Deterministic Artifact Sweep (`scripts/reproduce_all.sh`)
- **Command:** `WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (build Release, run FAST/SLOW tests + experiments).
- **Steps:** Build → run selected CTest labels → invoke experiment scripts below → write CSV/PNG under `docs/artifacts/` → update `docs/artifacts/manifest.json` via `manifest_utils`.
- **Outputs:** tri_engine_agreement.csv/png, qmc_vs_prng_equal_time.csv/png, mc_greeks_ci.csv/png, heston_qe_vs_analytic.csv/png, pde_order_slope.csv/png, ql_parity.csv/png, bench outputs, WRDS sample bundle, validation pack.

## WRDS OptionMetrics Pipeline (`python -m wrds_pipeline.pipeline`)
- **Single date (`run`)**
  - **Inputs:** symbol (default SPX), `trade_date`, `next_trade_date` (auto next business day), flags `--use-sample`, `--fast`, optional `--output-root`, label/regime tags. Requires WRDS env (`WRDS_ENABLED=1`, `WRDS_USERNAME`, `WRDS_PASSWORD`) unless `--use-sample`.
  - **Steps:** load_surface (WRDS or sample) → aggregate_surface (DTE≥21d, moneyness 0.75–1.25, IV/vega, tenor buckets) → calibrate_heston (least-squares IV, bootstrap CI, plots/tables) → calibrate_bs baseline → oos_pricing on next date → delta_hedge_pnl → summary/insample/OOS/hedge plots → manifest entry.
  - **Outputs:** per-date CSV/PNG under `docs/artifacts/wrds/per_date/<date>/` (fit table/json/fig, oos detail/summary, pnl detail/summary, surfaces). Summary fig `heston_wrds_summary.png`.
- **Panel (`run_dateset`)**
  - **Inputs:** `--dateset wrds_pipeline_dates_panel.yaml` (trade_date + next_trade_date + regime labels), optional `--use-sample/--fast/--output-root`.
  - **Steps:** loop `run` per date → aggregate to `wrds_agg_pricing.csv`, `wrds_agg_pricing_bs.csv`, `wrds_agg_oos.csv`, `wrds_agg_oos_bs.csv`, `wrds_agg_pnl.csv` → multi-date summary plot `wrds_multi_date_summary.png` → BS vs Heston comparison artifacts (`wrds_bs_heston_comparison.csv`, IVRMSE/OOS heatmap/PNL plots) via compare_bs_heston → manifest entry `runs.wrds_dateset`.
  - **Outputs:** Aggregated CSV/PNG under `docs/artifacts/wrds/`.

## Experiment Drivers (deterministic scenarios)
- **tri_engine_agreement.py** – Run analytic/MC/PDE on matched market params; writes agreement CSV/PNG.
- **qmc_vs_prng_equal_time.py** – Match wall-clock budgets between PRNG and Sobol+BB for European/Asian; outputs RMSE vs time CSV/PNG.
- **mc_greeks_ci.py** – Compare MC Greeks vs analytic bands; outputs estimator mean/SE/CI.
- **heston_qe_vs_analytic.py** – QE vs analytic CF sweep over parameter grids (base/stress/Feller); outputs price/IV RMSE CSV/PNG.
- **pde_order_slope.py** – Grid refinement study for CN; outputs convergence slope CSV/PNG.
- **ql_parity.py** – Compare quant_cli (BS, barrier PDE, American PSOR) vs QuantLib; outputs parity CSV/PNG.
- **american_consistency.py / parity_checks.py / greeks_reliability.py / greeks_variance.py / heston_series_plot.py / risk_backtest.py** – Smaller validation/diagnostic scripts; each reads deterministic inputs (often from `data/` or generated), runs quant_cli or internal formulas, emits CSV/plots noted in manifest.
- **generate_bench_artifacts.py** – Consumes Google Benchmark JSON to CSV/PNG (MC throughput, equal-time RMSE, PDE walltime/order, PSOR iterations).
- **package_validation.py** – Bundle docs/artifacts into `docs/validation_pack.zip` for releases.

## Python bindings walkthrough
- **Command:** `python -m python.examples.quickstart`  
- **Flow:** Calls pyquant_pricer BS functions, barrier RR, Heston helpers; optionally runs fast Heston calibration script if sample surfaces exist.
- **Outputs:** Console demo; optional Heston calibration PNG/CSV via scripts/calibrate_heston.py.

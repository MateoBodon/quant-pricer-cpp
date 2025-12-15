# Dataflow

## Locations
- `data/normalized/*.csv` – Normalized option surfaces (schema in `scripts/data/schema.md`); used by `scripts/calibrate_heston.py` and other calibration demos.
- `data/samples/spx_20240614_sample.csv` – Tiny synthetic SPX surface for fast smoke tests; also used by WRDS sample fallback.
- `docs/artifacts/` – Committed outputs (CSV/PNG, manifest.json, bench JSON/CSV, WRDS aggregates, logs). Subfolders:
  - `docs/artifacts/wrds/` – WRDS per-date (`per_date/`) and aggregated (`wrds_agg_*.csv`, comparison plots).
  - `docs/artifacts/bench/` – Google Benchmark raw JSON + derived CSV/PNG.
  - Other PNG/CSV from experiment scripts (tri_engine_agreement, qmc_vs_prng_equal_time, heston_qe_vs_analytic, pde_order_slope, mc_greeks_ci, ql_parity, etc.).
- `docs/artifacts/manifest.json` – Run metadata with git/system/build info and paths to generated artifacts.
- `build/`, `build-omp/` – CMake build trees (not part of data flow).

## Inputs → Processing → Outputs
- **Normalized surfaces (CSV, columns date, ttm_years, strike, mid_iv, put_call, spot, r, q, bid, ask)**  
  → `scripts/calibrate_heston.py` → calibrated params JSON, fit CSV/PNG in `artifacts/heston/`.

- **WRDS IvyDB / sample**  
  - `wrds_pipeline.ingest_sppx_surface.load_surface`: fetch WRDS table `optionm.opprcdYYYY` (when `WRDS_ENABLED=1` with credentials) or bundled sample CSV; adds spot/r/div defaults.  
  - `_prepare_quotes`: filter DTE ≥21d, price positivity, moneyness 0.75–1.25; compute IV via bs_utils.implied_vol_from_price; compute vega via bs_utils.bs_vega.  
  - `aggregate_surface`: bucket by tenor (30d,60d,90d,6m,1y) and moneyness (0.01 bins); average spot/strike/r/q/ttm/IV/vega; count quotes.
  - Outputs aggregated per-date surface CSVs (`<symbol>_<date>_surface.csv`).
  - **Calibration & evaluation:** `calibrate_heston` (IV least squares, bootstrap CI) + `calibrate_bs` (tenor σ baseline) → fitted surface tables/plots; `oos_pricing` → next-day detail/summary CSVs; `delta_hedge_pnl` → Δ‑hedged PnL detail/summary.
  - **Aggregation:** `pipeline.run_dateset` merges per-date outputs → `wrds_agg_pricing.csv`, `wrds_agg_pricing_bs.csv`, `wrds_agg_oos.csv`, `wrds_agg_oos_bs.csv`, `wrds_agg_pnl.csv` + summary/comparison PNGs.

- **Benchmark JSON (Google Benchmark)**  
  → `scripts/generate_bench_artifacts.py` → CSVs (`bench_mc_paths.csv`, `bench_pde_walltime.csv`, etc.) + PNGs under `docs/artifacts/bench/`.

- **Experiment outputs**  
  Deterministic scripts read synthetic parameters only; no external data. They emit CSV/PNG into `docs/artifacts/` and append manifest entries via `manifest_utils.update_run`.

## Environment & Paths
- WRDS access: `WRDS_ENABLED=1`, `WRDS_USERNAME`, `WRDS_PASSWORD`; optional `WRDS_CACHE_ROOT` to isolate outputs in tests; `--use-sample` bypasses credentials.
- Optional `WRDS_USE_SAMPLE=1` used by `scripts/reproduce_all.sh` to force deterministic sample panel.
- Build/test paths: `QUANT_BUILD_DIR` (manifest helper), `OMP_NUM_THREADS` (threading), CMake options (see CONFIG_REFERENCE).

## Data Assumptions
- Spot/strike positive; volatility caps in pipeline (IV clipped 0.05–3.0, rows hitting caps dropped).
- Moneyness trimmed to 0.75–1.25 with soft taper on weights; tenor buckets fixed list (30d/60d/90d/6m/1y).
- Tick size assumed 0.05 USD in WRDS + calibration scripts for price→tick conversions.

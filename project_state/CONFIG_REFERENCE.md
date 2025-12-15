# Config Reference

## Build / CMake
- `QUANT_ENABLE_OPENMP` (ON default) – enable OpenMP, defines `QUANT_HAS_OPENMP`.
- `QUANT_ENABLE_SANITIZERS` (OFF) – add ASan/UBSan flags when supported.
- `QUANT_ENABLE_CLANG_TIDY` (OFF) – run clang-tidy if found.
- `QUANT_ENABLE_PYBIND` (OFF by default in CMake, ON in `pyproject.toml` scikit-build) – build Python bindings.
- `CMAKE_BUILD_TYPE` (Release recommended for determinism/benchmarks).
- Env `QUANT_BUILD_DIR` – used by `manifest_utils` to read CMakeCache for compiler metadata.

## Environment
- `OMP_NUM_THREADS` – OpenMP thread override for MC/PDE/bench.
- `WRDS_ENABLED=1`, `WRDS_USERNAME`, `WRDS_PASSWORD` – enable live WRDS pulls; absent → sample fallback.
- `WRDS_CACHE_ROOT` – optional output root used by MARKET test to avoid polluting repo.
- `WRDS_USE_SAMPLE=1` – force sample pipeline inside `scripts/reproduce_all.sh`.

## CLI (`quant_cli`) Key Flags (per engine)
- `bs <S> <K> <r> <q> <σ> <T> <call|put> [--json]`
- `iv <call|put> <S> <K> <r> <q> <T> <price> [--json]`
- `mc <S> <K> <r> <q> <σ> <T> <paths> <seed> <antithetic0/1> <qmc> [bridge] [steps] [--greeks] [--ci] [--json] [--rng=counter|mt19937] [--threads=n]`
- `barrier bs|mc|pde ...` (adds barrier direction/style, B, rebate, grid/steps; `--cv` optional for mc KO only).
- `pde <S> <K> <r> <q> <σ> <T> <call|put> <M> <N> <Smax> [logspace] [neumann] [stretch] [theta flag] [rannacher] [--json]`
- `american binomial|psor|lsmc ...` (omega/tolerance/stretch options for PSOR; paths/steps/seed for LSMC).
- `asian`, `lookback`, `heston` (`--mc`, `--ci`, `--no-anti`, `--rng=`, `--heston-qe|--heston-euler`), `risk gbm ... [--json]`.

## WRDS Pipeline (`python -m wrds_pipeline.pipeline`)
- `--symbol` (default SPX), `--trade-date`, `--next-trade-date` (auto next biz day), `--use-sample`, `--fast`, `--dateset` (YAML/JSON list), `--output-root` (defaults `docs/artifacts/wrds`).
- Dateset file example: `wrds_pipeline_dates_panel.yaml` (trade_date, next_trade_date, label, regime, comment).

## Calibration Script (`scripts/calibrate_heston.py`)
- `--input <normalized_csv>` (schema in `scripts/data/schema.md`)
- `--fast` (fewer evals), `--metric price|vol`, `--seed`, `--retries`, `--param-transform none|exp|sigmoid`, `--weight-mode iv|price`.
- Outputs to `artifacts/heston/` (`params_<date>.json`, `fit_<date>.{csv,png}`); manifest updated.

## Experiment Scripts (selected)
- `qmc_vs_prng_equal_time.py` – `--output`, `--csv`, `--fast` (fewer reps).
- `heston_qe_vs_analytic.py` – `--output`, `--csv`, `--fast`, `--quant-cli`.
- `mc_greeks_ci.py` – `--output`, `--csv`, `--quant-cli`, optional `--paths`, `--seed`.
- `pde_order_slope.py` – `--output`, `--csv`, `--skip-build`.
- `ql_parity.py` – `--output`, `--csv`.
- `generate_bench_artifacts.py` – `--mc-json`, `--pde-json`, `--out-dir`.

## Data Schema
- Normalized surfaces: see `scripts/data/schema.md` (columns: date, ttm_years, strike, mid_iv, put_call, spot, r, q, bid, ask).
- WRDS ingest constraints: moneyness ∈ [0.75,1.25], DTE ≥21d, IV clipped (0.05–3.0), tick size 0.05.

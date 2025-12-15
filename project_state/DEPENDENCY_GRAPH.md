# Dependency Graph

### C++ Modules (headers/impl)
- `quant/math` ← none  
- `quant/stats` ← none  
- `quant/rng` ← `quant/math`
- `quant/black_scholes` ← `cmath`; used by `bs_barrier`, `pde_barrier`, CLI
- `quant/barrier` ← none; used by BS/MC/PDE/American
- `quant/term_structures` ← none; used by `mc`, `pde`
- `quant/grid_utils` ← `quant/barrier` (for OptionType)
- `quant/pde` ← `grid_utils`, `black_scholes` (boundary helpers), optional schedules
- `quant/pde_barrier` ← `pde`, `grid_utils`, `black_scholes`, `barrier`
- `quant/mc` ← `rng`, `math`, `stats`, `qmc/sobol`, `qmc/brownian_bridge`, `term_structures`
- `quant/mc_barrier` ← `mc` params, `barrier`, `black_scholes`, `math`, `qmc`
- `quant/asian` ← `math`, `stats`, `qmc/sobol`
- `quant/lookback` ← `math`, `stats`, `qmc/brownian_bridge`
- `quant/digital` ← `black_scholes`
- `quant/multi` ← `stats`
- `quant/american` ← `pde` (GridSpec/UpperBoundary), `grid_utils`, `barrier`
- `quant/risk` ← `math`, `stats` (Welford), uses `pcg_random`
- `quant/qmc/sobol` ← standalone
- `quant/qmc/brownian_bridge` ← standalone
- `quant/heston` ← `black_scholes` (implied vol), `math`, `stats`
- `src/main.cpp` (CLI) ← all above modules
- `python/pybind_module.cpp` ← all engine headers for bindings

### Python (WRDS & scripts)
- `wrds_pipeline/ingest_sppx_surface` ← `bs_utils` (IV/vega), pandas/numpy; optional psycopg2 for WRDS
- `wrds_pipeline/calibrate_heston` ← `bs_utils` (BS greeks/IV), `manifest_utils.update_run`; numpy/pandas/scipy/matplotlib
- `wrds_pipeline/calibrate_bs` ← `calibrate_heston._vega_quote_weights`, `bs_utils`
- `wrds_pipeline/oos_pricing` ← `calibrate_heston.apply_model`, `calibrate_heston.compute_oos_iv_metrics`
- `wrds_pipeline/delta_hedge_pnl` ← `bs_utils.bs_delta_call`
- `wrds_pipeline/compare_bs_heston` ← pandas/matplotlib; reads artifacts under `docs/artifacts/wrds/per_date`
- `wrds_pipeline/pipeline` ← `calibrate_heston`, `calibrate_bs`, `oos_pricing`, `delta_hedge_pnl`, `compare_bs_heston`, `ingest_sppx_surface`, `manifest_utils`
- `wrds_pipeline/tests/test_wrds_pipeline` ← pipeline CLI
- `scripts/*` drivers generally depend on `quant_cli` binary, `manifest_utils`, numpy/pandas/matplotlib/scipy/QuantLib` (per script) and optional WRDS artifacts.

### Core Hubs
- **C++ hubs:** `quant/mc`, `quant/pde`, `quant/american`, `quant/heston`, `quant/grid_utils`, `quant/black_scholes` are reused across CLI and bindings.  
- **Python hubs:** `calibrate_heston` (weights + metrics + model application), `manifest_utils` (artifact metadata), `pipeline` orchestrator.

### Notes
- No circular dependencies observed in C++; Python pipeline stays DAG-shaped (ingest → calibrate → oos/pnl → aggregate).
- Sobol supports only 64 dimensions; barrier MC uses 2 dims/step (normal + uniform), so `num_steps ≤ 32` when QMC is enabled.

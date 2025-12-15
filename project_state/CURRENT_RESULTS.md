# Current Results

- **Tri-engine parity (BS / MC / PDE)** – MC (200k paths, counter RNG, CV) and CN PDE agree with analytic BS within ≲5 bps across strikes; MC 95% CI overlays the PDE/analytic curves.  
  Sources: `docs/artifacts/tri_engine_agreement.{csv,png}`.

- **QMC vs PRNG (equal time)** – Sobol + Brownian bridge achieves ~1.4× lower RMSE than PRNG at matched wall-clock for European and Asian calls (fast mode).  
  Sources: `docs/artifacts/qmc_vs_prng_equal_time.{csv,png}`.

- **PDE convergence** – Crank–Nicolson with two Rannacher steps shows ~−2 slope on log–log error plots; price RMSE <1e-4 on a 401×400 grid; Δ/Γ within 1e-5 of BS.  
  Source: `docs/artifacts/pde_order_slope.{csv,png}`.

- **MC Greeks** – Pathwise Δ/ν, LRM Γ, mixed Γ, and Θ finite difference all fall within analytic 95% confidence bands at 200k paths.  
  Source: `docs/artifacts/mc_greeks_ci.{csv,png}`.

- **Heston QE vs analytic** – Updated QE (integrated-variance drift) reduces stress/Feller bias to <~1 price unit at 8–16 steps but base/ATM still shows ~4–6 price units bias at 64-step, 80k-path configs; IV RMSE tracked per scenario.  
  Source: `docs/artifacts/heston_qe_vs_analytic.{csv,png}`.

- **QuantLib parity** – Vanilla, barrier, and American prices match QuantLib within ≈$0.01; runtime deltas reported.  
  Source: `docs/artifacts/ql_parity/ql_parity.{csv,png}`.

- **Benchmarks** – OpenMP scaling near-linear 1→8 threads for MC throughput; QMC equal-time RMSE advantage retained after time-normalisation; PDE walltime/order plots accompany benchmark JSON.  
  Sources: `docs/artifacts/bench/bench_*.{json,csv,png}`.

- **WRDS OptionMetrics (bundled sample panel)** – Vega×quote-weighted in-sample IV RMSE ≈0.0160 vol pts (sample median), OOS IV MAE ≈127 bps, Δ‑hedged mean ≈ −12 ticks with σ 46–92 depending on tenor; BS baseline near parity in sample (`wrds_agg_pricing_bs.csv`, `wrds_agg_oos_bs.csv`).  
  Sources: `docs/artifacts/wrds/wrds_agg_pricing*.csv`, `wrds_agg_oos*.csv`, `wrds_agg_pnl.csv`, `wrds_bs_heston_comparison.csv`, summary PNGs.

- **Coverage** – Full gcovr HTML under `docs/coverage/` (line/function coverage high; branch coverage lower in barrier/risk/CLI paths).  
  Source: `docs/coverage/index.html`.

These results are deterministic for the bundled artifacts; rerun scripts for live WRDS data or alternative grids to update numbers.

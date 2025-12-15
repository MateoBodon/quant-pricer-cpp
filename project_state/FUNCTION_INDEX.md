# Function Index
Key functions/classes across C++ and Python sources. Arg types are schematic.

| File | Name | Type | Args (abbr.) | Returns | Description | Internal deps | External deps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| include/quant/math.hpp | inverse_normal_cdf | func | p: double | double | Acklam/Moro inverse Φ, used by RNG/QMC | – | std::erfc/log |
| include/quant/rng.hpp | uniform / normal | func | master_seed, path_id, step_id, dim_id, stream_id | double | Counter-based deterministic U(0,1)/N(0,1) draws | math::inverse_normal_cdf, splitmix64 | – |
| include/quant/stats.hpp | Welford | struct | add(value), merge(other) | mean/variance | Streaming moments for MC stats | – | – |
| include/quant/black_scholes.hpp | call_price / put_price | func | S,K,r,q,σ,T | double | Analytic BS PV with zero-T/σ guards | d1/d2 helpers | exp, erfc |
| include/quant/black_scholes.hpp | delta_call / gamma / vega / theta_call / rho_call | func | S,K,r,q,σ,T | double | PV Greeks (pathwise forms) | normal_pdf/cdf | – |
| include/quant/black_scholes.hpp | implied_vol_call | func | S,K,r,q,T,price | double | Brent root search in [1e-6,5]; NaN if no bracket | call_price | – |
| include/quant/bs_barrier.hpp | reiner_rubinstein_price | func | opt, barrier, S,K,r,q,σ,T | double | Closed-form knock-in/out with rebates and degenerate handling | bs::call/put | pow/erfc |
| include/quant/grid_utils.hpp | build_space_grid | func | StretchedGridParams | SpaceGrid | Uniform/log grid with tanh stretching | stretch_map | – |
| include/quant/grid_utils.hpp | assemble_operator | func | grid, DiffusionCoefficients, dt, θ, v_curr | OperatorWorkspace | Tridiagonal coefficients + RHS for CN/BW Euler | – | – |
| include/quant/pde.hpp | price_crank_nicolson | func | PdeParams | PdeResult {price,Δ,Γ,Θ?} | CN solver with Rannacher, optional schedules, interpolation | grid_utils, solve_tridiagonal, bs::dirichlet helper | – |
| include/quant/pde_barrier.hpp | price_barrier_crank_nicolson | func | BarrierPdeParams, opt | double | Log-space CN knock-out + parity for knock-in | pde::solve_tridiagonal, bs::call/put | – |
| include/quant/pde_barrier.hpp | price_barrier_crank_nicolson_greeks | func | BarrierPdeParams, opt | price,Δ,Γ | Three-point interpolation on KO grid; parity bump for KI | solve_knockout_grid | – |
| include/quant/mc.hpp | price_european_call | func | McParams | McResult{estimate} | GBM MC with antithetic, control variate, Sobol/BB, OpenMP | rng, qmc::Sobol, qmc::BrownianBridge, stats | pcg_random |
| include/quant/mc.hpp | greeks_european_call | func | McParams | GreeksResult{Δ,ν,Γ_LR,Γ_mix,Θ} | Pathwise/ LR estimators, common RNG Θ | rng, stats | pcg_random |
| include/quant/mc_barrier.hpp | price_barrier_option | func | McParams, K, opt, BarrierSpec | McResult | Barrier MC with Brownian-bridge crossing prob., optional CV (KO only) | rng, qmc::Sobol/BB, bs::call/put | pcg_random |
| include/quant/asian.hpp | price_mc | func | McParams | McStatistic | Arithmetic/geometric Asian MC with geometric CV, Sobol, antithetic | math::inverse_normal_cdf, stats | pcg_random |
| include/quant/lookback.hpp | price_mc | func | McParams | McStatistic | Lookback MC with optional Brownian bridge, antithetic | qmc::BrownianBridge, stats | pcg_random |
| include/quant/american.hpp | price_binomial_crr | func | Params, steps | double | CRR tree American price | intrinsic_value | – |
| include/quant/american.hpp | price_psor | func | PsorParams | PsorResult{price,iters,residual} | PSOR LCP on CN grid with Rannacher/stretch/Neumann options | grid_utils, pde-style operator | – |
| include/quant/american.hpp | price_lsmc | func | LsmcParams | LsmcResult{price,se,diagnostics} | Longstaff–Schwartz with polynomial regressors, ridge, ITM filter | pcg_random, stats | – |
| include/quant/american.hpp | greeks_psor_bump | func | PsorParams, rel_bump | {Δ,Γ} | Bump-and-reprice around spot using PSOR | price_psor | – |
| include/quant/multi.hpp | basket_european_call_mc | func | BasketMcParams | McStat | Correlated GBM basket via Cholesky, optional antithetic | stats | pcg_random |
| include/quant/multi.hpp | merton_call_mc | func | MertonParams | McStat | Jump-diffusion MC with Poisson jump count, antithetic | stats | pcg_random |
| include/quant/risk.hpp | var_cvar_from_pnl | func | pnl[], α | VarEs | Historical VaR/ES (alpha-tail) | sort | – |
| include/quant/risk.hpp | var_cvar_gbm / var_cvar_portfolio / var_cvar_t | func | market params, sims, seed, α | VarEs | Monte Carlo VaR/ES for single asset, Gaussian copula portfolio, Student‑t | math::inverse_normal_cdf | pcg_random, student_t |
| include/quant/risk.hpp | kupiec_christoffersen | func | exceptions[], α | BacktestStats | Kupiec POF + Christoffersen independence LR/p-values | chi2 tail helper | – |
| include/quant/heston.hpp | call_analytic | func | MarketParams, Params | double | CF-based Gauss–Laguerre call price (enforces intrinsic bound) | GL32 nodes/weights | std::complex |
| include/quant/heston.hpp | characteristic_function | func | u, mkt, Params | complex | Risk-neutral φ(u) matching analytic pricer | heston_phi | – |
| include/quant/heston.hpp | call_qe_mc | func | McParams | McResult | Andersen QE/Euler variance path MC with counter RNG, antithetic | rng, stats | pcg_random |
| wrds_pipeline/ingest_sppx_surface.py | load_surface | func | symbol, trade_date, force_sample | (DataFrame, source) | Fetch WRDS IvyDB or sample CSV; add spot/r/q, return raw quotes | bs_utils.implied_vol_from_price | psycopg2 (optional), pandas |
| wrds_pipeline/ingest_sppx_surface.py | aggregate_surface | func | raw_df | DataFrame | Filter DTE≥21d, moneyness 0.75–1.25, compute mid IV/vega, bucket tenor/moneyness | bs_utils.bs_vega | pandas/numpy |
| wrds_pipeline/calibrate_heston.py | calibrate | func | surface, CalibrationConfig | dict(params, surface, metrics, success) | Least-squares IV fit with bounded transform, apply model, metrics | _objective/_model_iv, compute_insample_metrics | scipy.least_squares, numpy |
| wrds_pipeline/calibrate_heston.py | bootstrap_confidence_intervals | func | surface, params, config | dict[key→(lo,hi)] | Resample/fit fast configs to derive 5–95% bands | calibrate | random, numpy |
| wrds_pipeline/calibrate_bs.py | fit_bs | func | surface | BsFit | Vega-weighted tenor σ baseline; metrics via calibrate_heston | calibrate_heston._vega_quote_weights | pandas |
| wrds_pipeline/oos_pricing.py | evaluate | func | oos_surface, params | (detail_df, summary_df, metrics) | Apply model to next-day surface; compute per-tenor MAE with weights | calibrate_heston.apply_model | pandas/numpy |
| wrds_pipeline/delta_hedge_pnl.py | simulate | func | today_df, tomorrow_df | (detail, summary) | Δ-hedged 1d PnL per tenor (ticks), quotes-weighted | bs_utils.bs_delta_call | pandas/numpy |
| wrds_pipeline/compare_bs_heston.py | generate_comparison_artifacts | func | artifacts_root, per_date_root | dict(paths) | Aggregate per-date insample/OOS/PNL, write comparison CSV + IVRMSE/OOS/PNL plots | pandas | matplotlib |
| wrds_pipeline/pipeline.py | run | func | symbol, trade_date, next_trade_date, use_sample, fast, output_dir?, label?, regime?, wrds_root? | dict(summary, artifacts, oos_summary, pnl_summary, bs_fit, bs_oos) | End-to-end single-date pipeline producing fit/OOS/PNL artifacts + manifest entry | calibrate_heston, calibrate_bs, oos_pricing, delta_hedge_pnl | pandas/matplotlib |
| wrds_pipeline/pipeline.py | run_dateset | func | symbol, dateset_path, use_sample, fast, output_root? | dict(paths) | Batch dateset processing → aggregated wrds_agg_pricing/oos/pnl + summary plot + comparison | run(), compare_bs_heston | pandas |
| scripts/manifest_utils.py | update_run | func | key, data, append=False, id_field=None | dict/ list | Persist run metadata into docs/artifacts/manifest.json with git/system/build info | ensure_metadata | subprocess, json |

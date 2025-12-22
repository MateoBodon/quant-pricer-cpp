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

# Function Index

## Python functions (AST-derived)
Derived from `project_state/_generated/symbol_index.json`.

### python.examples.quickstart (`python/examples/quickstart.py`)
- functions:
  - `price_vanilla()`
  - `price_barrier()`
  - `heston_helpers()`
  - `maybe_run_heston(repo_root)`
  - `main()`

### python.scripts.cibw_smoke (`python/scripts/cibw_smoke.py`)
- functions:
  - `main()`

### scripts.american_consistency (`scripts/american_consistency.py`)
- functions:
  - `american_put_psor(spec, m_nodes, n_steps, smax_mult=4.0, omega=1.5, tol=1e-08, max_iter=10000)`
  - `american_put_binomial(spec, steps)`
  - `american_put_lsmc(spec, paths, steps, seed)`
  - `main()`
- classes:
  - `AmericanSpec`

### scripts.build_wrds_cache (`scripts/build_wrds_cache.py`)
- functions:
  - `_today_utc()`
  - `_bdates(start, end)`
  - `_sha256(path)`
  - `_cache_path(cache_root, symbol, trade_date)`
  - `_cache_meta_path(cache_path)`
  - `_write_cache(cache_root, symbol, trade_date, df)`
  - `_load_dateset(path)`
  - `_require_wrds_env()`
  - `_iter_dates(args)`
  - `_write_manifest(cache_root, summary)`
  - `_append_index(index_path, entry)`
  - `_summarize_index(index_path)`
  - `main()`

### scripts.calibrate_heston (`scripts/calibrate_heston.py`)
- functions:
  - `black_scholes_call(spot, strike, r, q, sigma, T)`
  - `black_scholes_put(spot, strike, r, q, sigma, T)`
  - `implied_vol_from_price(price, spot, strike, r, q, T, is_call)`
  - `_heston_characteristic(phi, T, params, r, q, log_spot, j)`
  - `heston_call_price(spot, strike, r, q, T, params, n_points=256, phi_max=120.0)`
  - `_sigmoid_forward(value, lb, ub)`
  - `_sigmoid_inverse(value, lb, ub)`
  - `_compute_weight_vector(df, market_prices, vegas, mode)`
  - `_prepare_surface(df, fast)`
  - `_surface_market_prices(df)`
  - `_model_prices(df, params, fast)`
  - `calibrate_surface(df, config)`
  - `_plot_smiles(df, model_vols, output_path)`
  - `save_calibration_outputs(df, metrics, output_dir, fast)`
  - `main()`
- classes:
  - `CalibrationConfig`
  - `ParameterTransform`

### scripts.calibrate_heston_series (`scripts/calibrate_heston_series.py`)
- functions:
  - `resolve_inputs(inputs, pattern, input_dir)`
  - `main()`

### scripts.check_data_policy (`scripts/check_data_policy.py`)
- functions:
  - `_git_tracked_files()`
  - `_is_allowed_code_doc(path)`
  - `_is_guarded_data_file(path)`
  - `_requires_synthetic_marker(path)`
  - `_has_synthetic_marker(path)`
  - `_scan_lines(path)`
  - `main()`

### scripts.data.cboe_csv (`scripts/data/cboe_csv.py`)
- functions:
  - `_find_column(columns, candidates)`
  - `_normalized_put_call(raw)`
  - `_parse_date(value, fallback=None)`
  - `_parse_rate(series, default=0.0)`
  - `main()`

### scripts.data.wrds_fetch_options (`scripts/data/wrds_fetch_options.py`)
- functions:
  - `main()`

### scripts.data.wrds_fetch_returns (`scripts/data/wrds_fetch_returns.py`)
- functions:
  - `fetch_wrds(ticker, start, end)`
  - `fetch_yf(ticker, start, end)`
  - `main()`

### scripts.generate_bench_artifacts (`scripts/generate_bench_artifacts.py`)
- functions:
  - `load_benchmarks(path)`
  - `parse_mc(benches)`
  - `parse_pde(benches)`
  - `plot_throughput(df, out_path)`
  - `plot_rmse(df, out_path)`
  - `plot_equal_time(df, out_path)`
  - `plot_walltime(df, out_path)`
  - `plot_psor(df, out_path)`
  - `plot_order(df, out_path)`
  - `main()`

### scripts.generate_metrics_summary (`scripts/generate_metrics_summary.py`)
- functions:
  - `_safe_load_csv(path)`
  - `_rel_path(path)`
  - `_status_block(status, source, metrics=None, reason=None, notes=None)`
  - `_weighted_average(values, weights)`
  - `_regression_slope(x, y)`
  - `_required_artifact(name)`
  - `_required_path(name, artifacts_root)`
  - `_validate_required_artifacts(artifacts_root)`
  - `tri_engine_metrics(path)`
  - `qmc_vs_prng_metrics(path)`
  - `pde_order_metrics(path)`
  - `ql_parity_metrics(path)`
  - `_collapse_status(statuses)`
  - `benchmark_metrics(root)`
  - `_wrds_bundle_label(pricing_df)`
  - `wrds_metrics(root)`
  - `_fmt(value)`
  - `_highlights(name, block)`
  - `render_markdown(summary)`
  - `parse_args()`
  - `build_summary(artifacts_root, manifest_path)`
  - `main()`
- classes:
  - `RequiredArtifact`

### scripts.generate_synthetic_data (`scripts/generate_synthetic_data.py`)
- functions:
  - `bs_call(S, K, r, q, sigma, T)`
  - `make_options_csv(path)`
  - `make_returns_csv(path, days=1500)`
  - `main()`

### scripts.gpt_bundle (`scripts/gpt_bundle.py`)
- functions:
  - `_run_git(args)`
  - `_add_path(zf, path)`
  - `_render_required_paths(run_name)`
  - `_required_items(run_name)`
  - `_ticket_present(ticket_path, ticket_id)`
  - `_verify_zip(zip_path, required_paths)`
  - `_find_ticket_id(ticket_path)`
  - `_run_self_test()`
  - `main()`

### scripts.greeks_reliability (`scripts/greeks_reliability.py`)
- functions:
  - `_delta_pathwise(st, payoff_mask, spec, discount)`
  - `_delta_lr(payoff, z, spec, discount)`
  - `_delta_fd(payoff_up, payoff_dn, spec, discount)`
  - `_gamma_lr(payoff, z, spec, discount)`
  - `_gamma_fd(payoff_up, payoff, payoff_dn, spec, discount)`
  - `_simulate(n_paths, rng, spec)`
  - `_summaries(n_paths, samples)`
  - `_plot(df, output_png)`
  - `_parse_args()`
  - `_path_grid(args)`
  - `main()`
- classes:
  - `McSpec`

### scripts.greeks_variance (`scripts/greeks_variance.py`)
- functions:
  - `run_cli(cli, args)`
  - `main()`

### scripts.heston_qe_vs_analytic (`scripts/heston_qe_vs_analytic.py`)
- functions:
  - `_norm_cdf(x)`
  - `_bs_call_price(spot, strike, rate, div, vol, tenor)`
  - `_bs_vega(spot, strike, rate, div, vol, tenor)`
  - `_implied_vol_call(price, spot, strike, rate, div, tenor)`
  - `_find_quant_cli(override)`
  - `_run_cli_json(cli, args)`
  - `main()`

### scripts.heston_series_plot (`scripts/heston_series_plot.py`)
- functions:
  - `_parse_args()`
  - `_plot_params(df, output_png)`
  - `main()`

### scripts.manifest_utils (`scripts/manifest_utils.py`)
- functions:
  - `_rel_path(path)`
  - `_relativize_string(value)`
  - `_relativize_value(value)`
  - `_git_info()`
  - `_cpu_brand()`
  - `_system_info()`
  - `_omp_threads()`
  - `_cmake_value(lines, key)`
  - `_cmake_cache_path()`
  - `_compile_info()`
  - `load_manifest()`
  - `ensure_metadata(manifest)`
  - `save_manifest(manifest)`
  - `describe_inputs(paths)`
  - `update_run(key, data, append=False, id_field=None)`

### scripts.mc_greeks_ci (`scripts/mc_greeks_ci.py`)
- functions:
  - `_find_quant_cli(override)`
  - `_run_cli_json(cli, args)`
  - `_confidence_band(std_error)`
  - `main()`

### scripts.multiasset_figures (`scripts/multiasset_figures.py`)
- functions:
  - `ensure_matplotlib()`
  - `main()`

### scripts.package_validation (`scripts/package_validation.py`)
- functions:
  - `gather_files(artifacts, allowed_exts)`
  - `main(argv=None)`

### scripts.parity_checks (`scripts/parity_checks.py`)
- functions:
  - `black_scholes_call(S, K, r, q, sigma, T)`
  - `black_scholes_put(S, K, r, q, sigma, T)`
  - `black_scholes_digital_call(S, K, r, q, sigma, T)`
  - `build_grid(fast)`
  - `plot_results(df, output_path)`
  - `main()`

### scripts.pde_order_slope (`scripts/pde_order_slope.py`)
- functions:
  - `run(cmd, cwd=None)`
  - `black_scholes_call(S, K, r, q, sigma, T)`
  - `ensure_build(root, build_dir, skip)`
  - `main()`

### scripts.ql_parity (`scripts/ql_parity.py`)
- functions:
  - `_find_quant_cli(override)`
  - `_maturity_date(eval_date, tenor)`
  - `_build_process(spot, rate, dividend, vol, eval_date)`
  - `_scenarios(fast)`
  - `_run_cli(quant_cli, scenario)`
  - `_price_quantlib(scenario, eval_date)`
  - `_plot(df, out_path)`
  - `main()`
- classes:
  - `Scenario`

### scripts.qmc_vs_prng_equal_time (`scripts/qmc_vs_prng_equal_time.py`)
- functions:
  - `black_scholes_call(mkt)`
  - `simulate_call_price(mkt, normals)`
  - `simulate_asian_price(mkt, normals, steps)`
  - `generate_normals(paths, dims, method, seed)`
  - `estimator(mkt, paths, method, seed, kind, steps)`
  - `rmse_over_replicates(mkt, paths, method, kind, steps, reps, base_seed)`
  - `main()`
- classes:
  - `MarketSpec`

### scripts.report (`scripts/report.py`)
- functions:
  - `ensure_matplotlib()`
  - `run_cli(args)`
  - `price_heston_cli(cli_path, row, calib)`
  - `build_error_heatmap(cli_path, options_csv, calib_json, out_png)`
  - `build_iv_surface(options_csv, out_png)`
  - `build_param_series(series_csv, out_png)`
  - `build_var_plot(returns_csv, out_png, alpha=0.99)`
  - `stitch_pdf(artifacts_dir, images, pdf_name)`
  - `main()`

### scripts.risk_backtest (`scripts/risk_backtest.py`)
- functions:
  - `kupiec_pvalue(num_obs, num_exceed, alpha)`
  - `main()`

### scripts.sabr_slice_calibration (`scripts/sabr_slice_calibration.py`)
- functions:
  - `bs_price_call(S, K, r, q, sigma, T)`
  - `implied_vol_from_price(S, K, r, q, T, price)`
  - `hagan_black_vol(F, K, T, alpha, beta, rho, nu)`
  - `main()`

### scripts.tri_engine_agreement (`scripts/tri_engine_agreement.py`)
- functions:
  - `_bs_call(S, K, r, q, sigma, T)`
  - `_run(cmd)`
  - `_mc_price(quant_cli, spot, strike, r, q, sigma, T, paths, seed, steps)`
  - `_pde_price(quant_cli, spot, strike, r, q, sigma, T, nodes, timesteps)`
  - `build_dataset(quant_cli, strikes, spot, r, q, sigma, T, paths, seed, steps, nodes)`
  - `plot(df, out_path)`
  - `parse_args()`
  - `main()`

### tests.test_cli_fast (`tests/test_cli_fast.py`)
- functions:
  - `_norm_cdf(x)`
  - `_bs_common(spot, strike, rate, dividend, sigma, time)`
  - `bs_call_price(spot, strike, rate, dividend, sigma, time)`
  - `bs_put_price(spot, strike, rate, dividend, sigma, time)`
  - `cash_or_nothing_call(spot, strike, rate, dividend, sigma, time)`
  - `run_cli_plain(cli, *args)`
  - `run_cli_json(cli, *args)`
  - `assert_close(actual, expected, tol, msg)`
  - `assert_between(value, low, high, msg)`
  - `smoke_cli(cli)`
  - `main(argv=None)`

### tests.test_data_policy_fast (`tests/test_data_policy_fast.py`)
- functions:
  - `test_data_policy_guard()`

### tests.test_greeks_reliability_fast (`tests/test_greeks_reliability_fast.py`)
- functions:
  - `main()`

### tests.test_heston_fast (`tests/test_heston_fast.py`)
- functions:
  - `main()`

### tests.test_heston_safety_fast (`tests/test_heston_safety_fast.py`)
- functions:
  - `main()`

### tests.test_heston_series_fast (`tests/test_heston_series_fast.py`)
- functions:
  - `main()`

### tests.test_metrics_snapshot_fast (`tests/test_metrics_snapshot_fast.py`)
- functions:
  - `run_snapshot()`
  - `load_json(path)`
  - `assert_status_blocks(summary)`
  - `test_snapshot_outputs_exist_and_parse()`

### tests.test_parity_fast (`tests/test_parity_fast.py`)
- functions:
  - `main()`

### tests.test_qmc_fast (`tests/test_qmc_fast.py`)
- functions:
  - `main()`

### tools.project_state_generate (`tools/project_state_generate.py`)
- functions:
  - `_utc_now()`
  - `_git(cmd)`
  - `_rg_files()`
  - `_role_for_path(path)`
  - `_inventory()`
  - `_should_skip(path)`
  - `_iter_python_files()`
  - `_format_signature(node)`
  - `_collect_symbols(path)`
  - `_module_name(path)`
  - `_symbol_index()`
  - `_resolve_internal(module, modules)`
  - `_resolve_relative(current, level, module, name)`
  - `_import_graph(symbol_index)`
  - `_make_targets()`
  - `main()`
- classes:
  - `SymbolInfo`

### wrds_pipeline (`wrds_pipeline/__init__.py`)
- functions: (none)

### wrds_pipeline.bs_utils (`wrds_pipeline/bs_utils.py`)
- functions:
  - `_norm_cdf(x)`
  - `bs_call(spot, strike, rate, div, vol, T)`
  - `bs_put(spot, strike, rate, div, vol, T)`
  - `bs_delta_call(spot, strike, rate, div, vol, T)`
  - `bs_vega(spot, strike, rate, div, vol, T)`
  - `implied_vol_from_price(price, spot, strike, rate, div, T, option='call', tol=1e-06, max_iter=120)`

### wrds_pipeline.calibrate_bs (`wrds_pipeline/calibrate_bs.py`)
- functions:
  - `_weighted_mean_iv(group)`
  - `_apply_bs_surface(surface)`
  - `fit_bs(surface)`
  - `evaluate_oos(oos_surface, fit_vols)`
  - `summarize_oos(oos_surface)`
- classes:
  - `BsFit`

### wrds_pipeline.calibrate_heston (`wrds_pipeline/calibrate_heston.py`)
- functions:
  - `_heston_cf(u, T, params, r, q, log_spot)`
  - `heston_call_price(spot, strike, rate, div, T, params, n_points=32, phi_max=None)`
  - `_model_iv(row, params)`
  - `_positive_weights(values, default=1.0)`
  - `_moneyness_taper(surface)`
  - `_vega_quote_weights(surface, default=1.0)`
  - `_weighted_percentile(values, weights, percentile)`
  - `compute_insample_metrics(surface)`
  - `compute_oos_iv_metrics(surface)`
  - `_objective(params_vec, surface)`
  - `_to_internal(params)`
  - `_from_internal(internal)`
  - `_objective_internal(internal_vec, surface)`
  - `_params_tuple(params_dict)`
  - `apply_model(surface, params_dict)`
  - `calibrate(surface, config)`
  - `bootstrap_confidence_intervals(surface, params, config)`
  - `write_tables(out_csv, surface)`
  - `write_summary(out_json, payload)`
  - `plot_fit(surface, params, metrics, out_path)`
  - `record_manifest(out_json, summary, surface_csv, figure)`
- classes:
  - `CalibrationConfig`

### wrds_pipeline.compare_bs_heston (`wrds_pipeline/compare_bs_heston.py`)
- functions:
  - `_concat_csv(files)`
  - `_bucket_rmse(df, error_col, weight_col=None)`
  - `_bucket_mae(df, error_col, weight_col=None)`
  - `_load_insample(model)`
  - `_load_oos(model)`
  - `_load_pnl()`
  - `_aggregate_buckets()`
  - `_merge_comparison(buckets)`
  - `_plot_iv_rmse(comp, out_path)`
  - `_plot_oos_heatmap(oos_h, oos_b, out_path)`
  - `_plot_pnl_sigma(comp, out_path)`
  - `generate_comparison_artifacts(artifacts_root=WRDS_ROOT, per_date_root=PER_DATE_ROOT)`
  - `main()`

### wrds_pipeline.delta_hedge_pnl (`wrds_pipeline/delta_hedge_pnl.py`)
- functions:
  - `simulate(today, tomorrow)`
  - `write_outputs(detail_csv, summary_csv, detail, summary)`

### wrds_pipeline.ingest_sppx_surface (`wrds_pipeline/ingest_sppx_surface.py`)
- functions:
  - `_cache_root()`
  - `_local_root(explicit_root=None)`
  - `_local_optionm_root(local_root)`
  - `_local_opprcd_path(trade_date, local_root)`
  - `_local_secprd_path(trade_date, local_root)`
  - `_local_secnmd_path(local_root)`
  - `_resolve_secid_local(symbol, trade_date, local_root)`
  - `_fetch_from_local(symbol, trade_date, local_root)`
  - `_cache_path(symbol, trade_date)`
  - `_cache_meta_path(cache_path)`
  - `_load_cache(symbol, trade_date)`
  - `_write_cache(symbol, trade_date, df, source)`
  - `_has_wrds_credentials()`
  - `_table_for_trade_date(trade_date)`
  - `_secprd_table(trade_date)`
  - `_resolve_secid(conn, ticker, trade_date)`
  - `_fetch_from_wrds(symbol, trade_date)`
  - `_load_sample(symbol, trade_date)`
  - `load_surface(symbol, trade_date, force_sample=False, *, local_root=None)`
  - `_prepare_quotes(df)`
  - `aggregate_surface(df)`
  - `write_surface(out_path, df)`
  - `has_wrds_credentials(local_root=None)`

### wrds_pipeline.oos_pricing (`wrds_pipeline/oos_pricing.py`)
- functions:
  - `evaluate(oos_surface, params)`
  - `write_outputs(detail_csv, summary_csv, detail, summary)`

### wrds_pipeline.pipeline (`wrds_pipeline/pipeline.py`)
- functions:
  - `_next_business_day(trade_date)`
  - `_plot_wrds_summary(surface, oos, pnl, out_path)`
  - `_plot_insample_surface(surface, out_path)`
  - `_plot_oos_summary(oos, out_path)`
  - `_plot_hedge_distribution(pnl_detail, out_path)`
  - `_plot_multi_date_summary(pricing, oos, pnl, out_path)`
  - `_load_dateset_payload(path)`
  - `_local_root_from_payload(payload)`
  - `run(symbol, trade_date, next_trade_date, use_sample, fast, *, output_dir=None, label=None, regime=None, wrds_root=None, local_root=None)`
  - `run_dateset(symbol, dateset_path, use_sample, fast, *, output_root=None, local_root=None)`
  - `main()`

### wrds_pipeline.tests.test_wrds_pipeline (`wrds_pipeline/tests/test_wrds_pipeline.py`)
- functions:
  - `_root()`
  - `_has_wrds_env()`
  - `_expected_artifacts(base)`
  - `_write_dateset(path)`
  - `_baseline_sigma()`
  - `_assert_tolerances(wrds_root, dates)`
  - `main()`

## C++ API highlights (non-exhaustive)
- `quant::bs` (Black–Scholes) — price/greek helpers in `include/quant/black_scholes.hpp`.
- `quant::mc` — GBM/QMC Monte Carlo pricing + Greeks in `include/quant/mc.hpp`.
- `quant::pde` — Crank–Nicolson solvers in `include/quant/pde.hpp`.
- `quant::american`, `quant::barrier`, `quant::heston`, `quant::risk` — specialty engines in matching headers.

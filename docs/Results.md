# Results

`./scripts/reproduce_all.sh` builds the Release target, runs both FAST and SLOW labels, and regenerates deterministic CSV/PNG artifacts under `docs/artifacts/`. Use `REPRO_FAST=1` to trim runtime when iterating locally. Every generator updates [`artifacts/manifest.json`](artifacts/manifest.json) with the command, seeds, compiler info, and hardware snapshot.

## QMC vs PRNG RMSE Scaling

Sobol + Brownian bridge produces steeper log–log slopes than pseudorandom paths for both GBM vanillas and Asians, yielding roughly a 1.4× tighter RMSE at equal path budgets once paths exceed a few thousand.

![QMC vs PRNG](artifacts/qmc_vs_prng.png)

- Reproduce: `./scripts/reproduce_all.sh` or `python scripts/qmc_vs_prng.py --output docs/artifacts/qmc_vs_prng.png --csv docs/artifacts/qmc_vs_prng.csv --fast`
- Data: [artifacts/qmc_vs_prng.csv](artifacts/qmc_vs_prng.csv)
- Manifest entry: `runs.qmc_vs_prng`

## PDE Grid Convergence

Crank–Nicolson with two Rannacher steps retains ≈second-order accuracy as the spatial grid grows; price errors fall below 1e-4 on a 401×400 grid while Δ/Γ stay within 1e-5 of Black–Scholes.

![PDE grid convergence](artifacts/pde_convergence.png)

- Reproduce: `./scripts/reproduce_all.sh` or `python scripts/pde_convergence.py --skip-build --output docs/artifacts/pde_convergence.png --csv docs/artifacts/pde_convergence.csv`
- Data: [artifacts/pde_convergence.csv](artifacts/pde_convergence.csv)
- Manifest entry: `runs.pde_convergence`

## MC Greeks with 95% CI

Counter-based RNG plus antithetic sampling keeps the LR Theta/Vega and mixed-pathwise Gamma within analytic 95% bands at 200k paths, and the CSV captures per-estimator standard errors for downstream dashboards.

![MC Greeks CI](artifacts/mc_greeks_ci.png)

- Reproduce: `./scripts/reproduce_all.sh` or `python scripts/mc_greeks_ci.py --quant-cli build/quant_cli --output docs/artifacts/mc_greeks_ci.png --csv docs/artifacts/mc_greeks_ci.csv`
- Data: [artifacts/mc_greeks_ci.csv](artifacts/mc_greeks_ci.csv)
- Manifest entry: `runs.mc_greeks_ci`

## Heston QE vs Analytic

Current QE runs still exhibit a large bias versus the analytic reference (CLI emits warnings in the log), so the plot captures that divergence alongside the Euler baseline. Keeping the CSV/manifest entries in-tree lets us spot the eventual QE regression fix—once the bias shrinks, the same plot will show the intended log–log convergence.

![Heston QE vs analytic](artifacts/heston_qe_vs_analytic.png)

- Reproduce: `./scripts/reproduce_all.sh` or `python scripts/heston_qe_vs_analytic.py --quant-cli build/quant_cli --output docs/artifacts/heston_qe_vs_analytic.png --csv docs/artifacts/heston_qe_vs_analytic.csv`
- Data: [artifacts/heston_qe_vs_analytic.csv](artifacts/heston_qe_vs_analytic.csv)
- Manifest entry: `runs.heston_qe_vs_analytic`

## WRDS OptionMetrics Snapshot (Opt-in)

The WRDS pipeline ingests a single SPX trading day (OptionMetrics), bins mid IVs by tenor/moneyness, performs a coarse Heston calibration, and emits only aggregated diagnostics. MARKET tests (`ctest -L MARKET`) are gated by `WRDS_ENABLED=1` plus credentials; without them we fall back to the bundled sample file so the CSVs stay reproducible.

- Surface buckets: [artifacts/wrds/spx_surface_sample.csv](artifacts/wrds/spx_surface_sample.csv)
- Calibration summary: [artifacts/wrds/heston_calibration_summary.csv](artifacts/wrds/heston_calibration_summary.csv)
- OOS diagnostics: [artifacts/wrds/oos_pricing.csv](artifacts/wrds/oos_pricing.csv) / [artifacts/wrds/oos_pricing_summary.csv](artifacts/wrds/oos_pricing_summary.csv)
- Delta hedge trace: [artifacts/wrds/delta_hedge_pnl.csv](artifacts/wrds/delta_hedge_pnl.csv)

Regenerate offline with `RUN_WRDS_PIPELINE=1 ./scripts/reproduce_all.sh` (forces the sample fallback) or call `python wrds_pipeline/pipeline.py --use-sample` directly. Remove `--use-sample` and export the WRDS env vars to hit the live database.

## Manifest & determinism

[`artifacts/manifest.json`](artifacts/manifest.json) records the git SHA, compiler/flag metadata, CPU info, RNG modes, and the exact CLI invocations behind every plot above. CI appends to the same manifest so reviewers can diff the bundle before shipping changes.

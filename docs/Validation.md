# Validation Summary

## Analytic Cross-Checks
- **Put–Call Parity**: Unit tests assert analytic parity for BS prices and thetas to 1e-10.
- **MC Variance Reduction**: GTest ensures antithetic and control variate usage decreases the MC standard error relative to vanilla PRNG.
- **PDE Accuracy**: Log–log convergence tests confirm second-order spatial accuracy; additional tests verify Dirichlet and Neumann boundaries match Black–Scholes calls, and Rannacher start-up halves the pricing error versus pure CN.
- **Barrier In/Out Parity**: Analytic `in + out = vanilla` identity is exercised for down-and-out calls at 1e-8 tolerance.
- **American Consistency**: Binomial, PSOR, and LSMC agree within PSOR tolerance / LSMC SE for American puts with dividends.

## Demo Artifacts (see `./scripts/demo.sh`)
- `qmc_vs_prng.png`: RMSE decay (paths vs error) comparing PRNG and Sobol+Brownian bridge; shows Sobol achieving ~2× lower RMSE at equal paths.
- `pde_convergence.png`: Price error vs grid nodes validating ≈2nd order slope and Rannacher smoothing.
- `american_convergence.png`: PSOR versus binomial convergence plus LSMC scatter overlay (3σ band) for early-exercise options.
- `barrier_validation.png`: Log-scale absolute error comparison for barrier MC/PDE vs Reiner–Rubinstein benchmarks.
- `onepager.pdf`: Single-page summary combining the above plots, a Greeks variance table, and benchmark stats for quick reviewer digestion.

## Benchmarks
- **MC Throughput**: `bench_mc` reports paths/s vs thread count and standard error comparison between PRNG and Sobol+BB at equal wall-time.
- **PDE Timing**: `bench_pde` measures wall-time as grids refine (101×100 → 321×320) and records PSOR iteration counts across ω settings.

## CLI Regression
- CLI regression options `--sampler`, `--bridge`, `--steps`, `--threads`, and `--json` are covered in integration tests via the demo script to ensure consistent formatting and deterministic results.

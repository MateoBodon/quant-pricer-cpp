# Validation Summary

## Analytic Cross-Checks
- **Put–Call Parity**: Unit tests assert analytic parity for BS prices and thetas to 1e-10.
- **MC Variance Reduction**: GTest ensures antithetic and control variate usage decreases the MC standard error relative to vanilla PRNG.
- **PDE Accuracy**: Log–log convergence tests confirm second-order spatial accuracy; additional tests verify Dirichlet and Neumann boundaries match Black–Scholes calls, and Rannacher start-up halves the pricing error versus pure CN.
- **Barrier In/Out Parity**: Analytic `in + out = vanilla` identity is exercised for down-and-out calls at 1e-8 tolerance.
- **American Consistency**: Binomial, PSOR, and LSMC agree within PSOR tolerance / LSMC SE for American puts with dividends.

## Validation Artifacts (see `./scripts/reproduce_all.sh`)
- `qmc_vs_prng_equal_time.png`: RMSE vs wall-clock comparing PRNG and Sobol+Brownian bridge; the committed metrics snapshot reports a median PRNG/QMC RMSE ratio of 4.76346 for the tested scenarios.
- `pde_order_slope.png`: Price error vs grid nodes validating ≈2nd order slope and Rannacher smoothing.
- American option consistency is covered by FAST tests comparing PSOR, binomial, and LSMC paths.
- Barrier pricing consistency is covered by FAST tests comparing MC/PDE paths against Reiner-Rubinstein benchmarks.

`docs/artifacts/manifest.json` accompanies every run. It captures the compiler, build flags,
platform details, all CLI invocations issued by the script, and the seeds/paths used
for each scenario (including the new LSMC diagnostics: ITM counts, regression sample
sizes, and basis condition numbers per exercise date).

### Barrier MC accuracy notes
- The Brownian-bridge crossing correction greatly reduces time-discretization bias for continuously-monitored single barriers. Residual error is dominated by Monte Carlo variance; increase `num_steps` (e.g., 64–256) and `paths` to tighten agreement with RR analytics. Prefer `--sampler=sobol --bridge=bb` for faster convergence on multi-step paths.
- Reviewer summaries should be regenerated from the current tracked artifacts; no committed `onepager.pdf` is part of the current curated artifact set.

## Benchmarks
- **MC Throughput**: `bench_mc` reports paths/s vs thread count and standard error comparison between PRNG and Sobol+BB at equal wall-time.
- **PDE Timing**: `bench_pde` measures wall-time as grids refine (101×100 → 321×320) and records PSOR iteration counts across ω settings.

## CLI Regression
- CLI regression options `--sampler`, `--bridge`, `--steps`, `--threads`, and `--json` are covered in integration tests via the reproduction script to ensure consistent formatting and deterministic results.

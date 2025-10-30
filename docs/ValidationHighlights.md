# Validation Highlights (current `scripts/demo.sh` bundle)

This document distills the highest-leverage outputs emitted by `scripts/demo.sh`.
Regenerate it after significant algorithmic changes:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./scripts/demo.sh
```

All raw CSVs/PNGs/PDFs live in `artifacts/`, while `artifacts/manifest.json`
now records the git SHA, compiler, build flags, platform details, every CLI
command executed by the demo script, and the seeds/resolutions used for each
pricing sweep.

## Highlights at a glance

- **Deterministic Monte Carlo:** Counter-based RNG (`rng: "counter"`) makes
  serial and parallel executions bitwise-identical. `tests/test_rng_repro.cpp`
  enforces this across {1,4,8} threads.
- **Heston Andersen QE:** `artifacts/heston_qe_convergence.csv` and
  `heston_qe_convergence.png` compare QE vs Euler against the analytic
  characteristic-function price across 16–128 time steps.
- **Greeks with Confidence Bands:** `artifacts/greeks_ci.csv` records Delta,
  Vega, Gamma (LR + mixed), and Theta (LR) with standard errors and 95 % CIs.
  The companion PNG visualises the bands and spotlights estimator stability.
- **Offline-safe artifacts:** The demo script never `pip install`s matplotlib.
  If plotting libraries are absent it still writes every CSV, logging which PNG/
  PDF outputs were skipped.

## Vanilla cross-checks

- `artifacts/black_scholes.csv` confirms the ATM 100/100 call and put match
  analytic values to machine precision.
- `artifacts/monte_carlo.csv` captures the GBM control-variate run (counter RNG,
  antithetic) together with standard errors and confidence intervals.

## Sobol vs PRNG RMSE

`artifacts/qmc_vs_prng.csv` shows Sobol + Brownian bridge consistently cutting
RMSE by ~1.4× versus Euler + PRNG across 20 000–320 000 paths. The manifest’s
`qmc_vs_prng` section includes both RMSEs and the CI bands.

## PDE convergence

`artifacts/pde_convergence.csv` reports Crank–Nicolson + Rannacher error slopes
(≈−2.0 on recent runs). Δ/Γ remain within ≈2×10⁻⁵ of Black–Scholes once the grid
exceeds 201×200; 801×400 pushes price errors below 1e-4.

## Barrier validation

`artifacts/barrier_validation.csv` documents Monte Carlo (no terminal-stock
control variate) versus Reiner–Rubinstein closed forms. The PNG provides the
log-scale comparison against the PDE benchmark.

## American option validation

`artifacts/american_validation.csv` logs PSOR residuals/iteration counts,
binomial convergence, and LSMC standard errors. The manifest mirrors the run
metadata (paths, steps, seed) alongside the per-exercise ITM counts and basis
condition numbers produced by the new diagnostics—handy for regression testing
and resume-ready plots.

## Heston QE

`artifacts/heston_qe_convergence.csv` compares Andersen QE and Euler schemes
for a representative parameter set (80 000 paths, counter RNG). Expect QE to sit
inside the analytic confidence band as steps increase, while Euler converges
noticeably slower.

## Greeks (CI aware)

`artifacts/greeks_ci.csv` + `.png` detail Delta/Vega/Gamma/Theta estimates,
their standard errors, and 95 % confidence intervals, enabling direct
comparison with Black–Scholes analytics.

## Artifact index

- `artifacts/manifest.json` – reproducibility metadata (compiler, flags,
  platform, executed commands, MC/Heston/Greeks/American seeds & summaries).
- `qmc_vs_prng.csv` / `.png` – MC RMSE comparison.
- `heston_qe_convergence.csv` / `.png` – Andersen QE vs Euler convergence.
- `greeks_ci.csv` / `.png` – LR/pathwise Greeks with confidence bands.
- `pde_convergence.csv` / `.png` – log–log error slopes for Crank–Nicolson.
- `american_convergence.csv` / `.png` – PSOR/binomial/LSMC agreement.
- `barrier_validation.csv` / `.png` – MC + PDE vs Reiner–Rubinstein.

> Regenerate with `./scripts/demo.sh` whenever pricing engines or RNGs change
> so recruiters and reviewers always see current evidence.

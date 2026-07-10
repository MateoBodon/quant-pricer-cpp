# Validation Highlights

This document distills the highest-leverage committed artifacts under `docs/artifacts/`. The latest committed metrics snapshot was generated on 2026-01-25; the 2026-07-03 T-001/T-101 current-HEAD reproduction attempt failed during FAST and did not promote regenerated artifacts. Regenerate after significant algorithmic changes:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./scripts/reproduce_all.sh
```

Tracked CSV/PNG/JSON artifacts live in `docs/artifacts/`, while `docs/artifacts/manifest.json` records the git SHA, compiler, build flags, platform details, commands, and seeds/resolutions used for each pricing sweep. Ignored WRDS detail files are not current public evidence.

## Highlights at a glance

- **Deterministic Monte Carlo:** Counter-based RNG (`rng: "counter"`) makes
  serial and parallel executions bitwise-identical. `tests/test_rng_repro.cpp`
  enforces this across {1,4,8} threads.
- **Heston Andersen QE:** `docs/artifacts/heston_qe_vs_analytic.csv` and
  `docs/artifacts/heston_qe_vs_analytic.png` compare QE/Euler Monte Carlo against the analytic
  characteristic-function price; QE remains caveated by known bias.
- **Greeks with Confidence Bands:** `docs/artifacts/mc_greeks_ci.csv` records Delta,
  Vega, Gamma (LR + mixed), and Theta (LR) with standard errors and 95 % CIs.
  The companion PNG visualises the bands and spotlights estimator stability.
- **Offline-safe artifacts:** The reproduction script never `pip install`s matplotlib.
  If plotting libraries are absent it still writes every CSV, logging which PNG/
  PDF outputs were skipped.

## Sobol vs PRNG (equal time)

`docs/artifacts/qmc_vs_prng_equal_time.csv` shows Sobol + Brownian bridge delivering lower RMSE than pseudorandom paths in the tested scenarios. The committed metrics snapshot reports the metric as a PRNG/QMC RMSE ratio: 4.76346 median overall. The manifest's `qmc_vs_prng_equal_time` section records the time grid, per-method RMSE curves, and seeds.

## PDE convergence

`docs/artifacts/pde_order_slope.csv` reports Crank–Nicolson + Rannacher error slopes
(≈−2.0 on recent runs). Δ/Γ remain within ≈2×10⁻⁵ of Black–Scholes once the grid
exceeds 201×200; 801×400 pushes price errors below 1e-4.

## Barrier validation

Barrier validation is covered by FAST tests against Reiner-Rubinstein closed forms. No current tracked `barrier_validation.*` artifact is part of the curated artifact set.

## American option validation

American option consistency is covered by FAST tests for PSOR, binomial, and LSMC agreement. No current tracked `american_validation.*` artifact is part of the curated artifact set.

## Heston QE

`docs/artifacts/heston_qe_vs_analytic.csv` compares Andersen QE and Euler schemes against analytic Heston prices across representative parameter sets (80,000 paths, counter RNG). Treat QE as experimental/caveated until a dedicated Heston credibility ticket resolves the known bias.

## Greeks (CI aware)

`docs/artifacts/mc_greeks_ci.csv` + `.png` detail Delta/Vega/Gamma/Theta estimates,
their standard errors, and 95 % confidence intervals, enabling direct
comparison with Black–Scholes analytics.

## Artifact index

- `docs/artifacts/manifest.json` – reproducibility metadata (compiler, flags,
  platform, executed commands, MC/Heston/Greeks/American seeds & summaries).
- `qmc_vs_prng_equal_time.csv` / `.png` - equal-time MC RMSE comparison.
- `heston_qe_vs_analytic.csv` / `.png` - QE/Euler Monte Carlo vs analytic Heston.
- `mc_greeks_ci.csv` / `.png` - LR/pathwise Greeks with confidence bands.
- `pde_order_slope.csv` / `.png` - log-log error slopes for Crank-Nicolson.
- `tri_engine_agreement.csv` / `.png` - analytic/MC/PDE agreement.
- `ql_parity/ql_parity.csv` / `.png` - QuantLib parity.

> Regenerate with `./scripts/reproduce_all.sh` whenever pricing engines or RNGs change
> so recruiters and reviewers always see current evidence.

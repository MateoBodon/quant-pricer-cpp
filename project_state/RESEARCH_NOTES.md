# Research Notes

## Problem & Framework
The library prices equity-style derivatives under risk-neutral GBM and Heston dynamics, exposing Greeks, hedging metrics, and validation/benchmark harnesses. It emphasizes cross-validation between analytic, Monte Carlo, and finite-difference PDE engines to catch numerical or modeling drift.

## Concepts / Glossary
- **Black–Scholes (BS)**: Lognormal GBM, closed-form European prices and Greeks; implied vol inversion via Brent.
- **Crank–Nicolson (CN) PDE**: Second-order finite-difference scheme for backward pricing; Rannacher start-up stabilizes payoff kink; tanh grid stretching clusters points near strike; Dirichlet or Neumann upper boundary.
- **Variance Reduction**: Antithetic variates; control variate on discounted terminal spot; Sobol QMC (scrambled) with Brownian bridge to reduce effective dimension; streaming Welford statistics for CI.
- **Barrier crossing (MC)**: Brownian-bridge crossing probability `p = exp(-2 log(B/S_t) log(B/S_{t+Δt}) / (σ² Δt))` sampled per step (clamped) to correct discretization bias.
- **American early exercise**: PSOR solves LCP on CN grid; LSMC regressions on polynomial basis with ridge, ITM filters, condition numbers tracked.
- **Heston**: Stochastic variance CIR process; analytic call via characteristic function and 32-pt Gauss–Laguerre; QE MC uses conditional moments with regime switch on ψ, Euler fallback.
- **Risk metrics**: VaR/CVaR (historical, GBM MC, Gaussian copula portfolio, Student‑t), Kupiec/Christoffersen backtests.

## Algorithm ↔ Code Pointers
- BS formulas & Greeks: `include/quant/black_scholes.hpp`, `src/black_scholes.cpp`; implied vols use bracketed Brent, guard intrinsic bounds.
- PDE CN assembly: `quant/grid_utils::assemble_operator`, `quant/pde::price_crank_nicolson` (interpolated Δ/Γ, optional Θ by backward diff).
- Barrier CN: `quant/pde_barrier` builds one-sided log grid, parity for knock-in; interpolation for Greeks.
- MC GBM: `quant/mc::price_european_call` (bridge/QMC/control variate), Greeks in `quant/mc::greeks_european_call` (pathwise Δ/ν, LRM Γ, mixed Γ = Δ·score − second bump).
- Barrier MC: `quant/mc_barrier::price_barrier_option` applies Brownian-bridge crossing probability and parity; disables CV for knock-in to avoid bias.
- Asian MC: geometric control variate (Kemna–Vorst) implemented in `src/asian.cpp`.
- American PSOR/LSMC: `src/american.cpp` with stretched/log grids, ω relaxation, residual/tolerance stopping; LSMC stores regression diagnostics to detect ill-conditioning.
- Heston analytic & QE: `src/heston.cpp` matches QE drift to Andersen’s integrated variance; CF in `characteristic_function`; known residual bias remains for ATM base scenarios.
- WRDS calibration: `wrds_pipeline/calibrate_heston.py` mirrors C++ GL32 CF (bounded params, IV least squares, bootstrap CIs); weights = vega × quotes × wing taper.

## Open/uncertain points
- QE bias persists in base/ATM high vol-of-vol despite integrated-drift fix—may require martingale correction or alternative time discretization.
- WRDS pipeline uses vega×quote weights with wing taper; alternative weighting (liquidity-adjusted or joint price/IV target) could change conclusions.
- Sobol dimension cap (64) constrains barrier MC steps when using QMC (2 dims per step).

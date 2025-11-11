# Changelog

## Unreleased

- feat(heston,mc): Andersen QE variance paths, deterministic counter RNG, CLI/pybind confidence intervals for MC Greeks

## v0.2.0

- Advanced MC: Sobol (optional Owen/digital shift) + Brownian bridge; antithetic/control variates; mixed Γ estimator
- Barriers: Reiner–Rubinstein analytics, Brownian-bridge MC crossing, absorbing-boundary PDE
- American options: PSOR (finite-difference LCP) and Longstaff–Schwartz MC with polynomial basis
- PDE: Crank–Nicolson with Rannacher start, Dirichlet/Neumann boundaries; Δ/Γ via 3‑point central, optional Θ via backward differencing
- Reproducible demo: artifacts include qmc_vs_prng_equal_time.png, pde_order_slope.png, barrier_validation.png, american_convergence.png, onepager.pdf, manifest.json
- CLI: modern flags (--sampler/--bridge/--steps/--threads/--json) with legacy positional retained
- Docs: API hosted via GitHub Pages (Doxygen); README artifacts index and usage
- Consumer example: examples/consumer-cmake with find_package support

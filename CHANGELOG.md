# Changelog

## Unreleased

- feat(heston,mc): Andersen QE variance paths, deterministic counter RNG, CLI/pybind confidence intervals for MC Greeks

## v0.3.1

- test(cli): added `cli_smoke_fast` to exercise every quant_cli engine under JSON output and committed the full gcovr HTML bundle so `/coverage/` on gh-pages stays live.
- chore(release): new `scripts/package_validation.py` plus a release workflow that runs `scripts/reproduce_all.sh` (sample WRDS bundle) and uploads `docs/validation_pack.zip` alongside `docs/artifacts/manifest.json`.
- build: bumped the CMake/project/python package versions to 0.3.1 so wheels + docs advertise the new release.

## v0.3.0

- feat(python): pybind bindings now expose Heston characteristic function/implied vol plus PDE + MC stats; `python/examples/quickstart.py` demonstrates the helpers.
- feat(heston): Added public `characteristic_function` and `implied_vol_call` APIs with unit tests (phi(0)=1, BS parity).
- ci(packaging): cibuildwheel workflow now builds Linux/macOS/Windows wheels and runs a smoke test; consumer CMake example builds in CI to guard install export.
- build: bumped project + Python package version to 0.3.0, documented `pip install pyquant-pricer`, and added `python/scripts/cibw_smoke.py`.

## v0.2.0

- Advanced MC: Sobol (optional Owen/digital shift) + Brownian bridge; antithetic/control variates; mixed Γ estimator
- Barriers: Reiner–Rubinstein analytics, Brownian-bridge MC crossing, absorbing-boundary PDE
- American options: PSOR (finite-difference LCP) and Longstaff–Schwartz MC with polynomial basis
- PDE: Crank–Nicolson with Rannacher start, Dirichlet/Neumann boundaries; Δ/Γ via 3‑point central, optional Θ via backward differencing
- Reproducible demo: artifacts include qmc_vs_prng_equal_time.png, pde_order_slope.png, barrier_validation.png, american_convergence.png, onepager.pdf, manifest.json
- CLI: modern flags (--sampler/--bridge/--steps/--threads/--json) with legacy positional retained
- Docs: API hosted via GitHub Pages (Doxygen); README artifacts index and usage
- Consumer example: examples/consumer-cmake with find_package support

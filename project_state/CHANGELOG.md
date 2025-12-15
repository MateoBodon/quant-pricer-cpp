# Changelog (summary)

_Source of truth: root `CHANGELOG.md`._

- **Unreleased** – Further Heston/QE work (Andersen QE variance paths, counter RNG, MC Greek CIs via CLI/pybind) in progress.

- **v0.3.2**
  - WRDS panel pipeline (multi-date OptionMetrics with vega-weighted RMSE/MAE, OOS bps, Δ‑hedged PnL) and deterministic sample bundle.
  - Google Benchmark refresh + plots (OpenMP throughput, equal-time RMSE, PDE −2 slope) wired into docs/manifest.
  - QuantLib parity script + published CSV/PNG.
  - Docs/Pages pipeline now publishes artifacts + coverage; project/python versions bumped to 0.3.2.

- **v0.3.1**
  - Added `cli_smoke_fast` test; committed gcovr HTML bundle to gh-pages.
  - `scripts/package_validation.py` + release workflow to ship validation pack alongside artifacts.
  - Version bumps to 0.3.1 across CMake/pyproject/setup.

- **v0.3.0**
  - Pybind bindings expose Heston CF/implied vol + PDE/MC stats; quickstart example.
  - Public Heston CF/IV C++ APIs with unit tests.
  - cibuildwheel builds (Linux/macOS/Windows) with smoke tests; consumer CMake example in CI.
  - Version bumps to 0.3.0; README documents pip install.

- **v0.2.0**
  - Added Sobol QMC + Brownian bridge; control/antithetic variates; mixed Γ estimator.
  - Barrier analytics/MC/PDE; American PSOR/LSMC; CN PDE with Rannacher and boundaries; parity/validation figures.
  - CLI modern flags; API docs/gh-pages; deterministic artifacts and manifest.

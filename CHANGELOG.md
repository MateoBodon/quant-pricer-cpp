# Changelog

## Unreleased

- feat(heston,mc): Andersen QE variance paths, deterministic counter RNG, CLI/pybind confidence intervals for MC Greeks
- ops(gpt-bundle): hard-gate empty run logs and include base commit diffs + commit lists in GPT bundles
- ops(artifacts): reproduce_all now builds full QL parity/bench/WRDS sample evidence before metrics snapshot, and metrics generation hard-fails when required artifacts are missing; validation pack is emitted at the end of the run
- ops(artifacts): enforce canonical manifest usage in metrics summaries and add a FAST guard against `artifacts/` writes (tests now emit to temp outputs)
- ops(data-policy): enforce `# SYNTHETIC_DATA` markers for sample CSVs, regenerate synthetic WRDS sample data, and skip comment lines in sample loading
- dev(test): add `requirements-dev.txt` and document test dependencies (matplotlib included)
- wrds(cache): add WRDS parquet cache support and a bulk cache builder script for real-data slices
- wrds(local): document local WRDS OptionMetrics parquet stash and include a manifest in the validation bundle
- wrds(local): require explicit WRDS_LOCAL_ROOT / dateset config for local mode, keep sample artifacts as default, and scrub repo-relative paths in committed artifacts
- wrds(validity): hard-fail as-of correctness checks for calibration/OOS and add poison FAST coverage (with `WRDS_SAMPLE_PATH` override)
- wrds(panel): make `wrds_pipeline_dates_panel.yaml` the canonical panel config and log `panel_id` in WRDS provenance
- wrds(panel): require `panel_id` in dateset configs (no legacy `dataset_id`) and record data mode + date ranges in WRDS provenance
- docs(project_state): refresh project_state docs and generated indices
## v0.3.2

- feat(wrds): multi-date OptionMetrics panel (vega-weighted RMSE/MAE, OOS bps, Δ-hedged PnL) with aggregated CSV/PNG artifacts, manifest updates, and deterministic sample bundle.
- bench: refreshed Google Benchmark harness + plots (OpenMP throughput, equal-time Asian/Barrier, PDE −2 slope) and wired the data into the docs + manifest.
- docs(parity): added `scripts/ql_parity.py` to diff quant-pricer against QuantLib (vanilla/barrier/American) with published CSV/PNG + manifest entry.
- docs(pages): Pages workflow now copies `docs/artifacts/` + coverage HTML, injects `<base href='/quant-pricer-cpp/'>`, disables Jekyll, and README badges link to the live Results and coverage pages.
- build/release: bumped the project/pybind/setup versions to 0.3.2 so wheels, CMake, and docs advertise the new release.

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

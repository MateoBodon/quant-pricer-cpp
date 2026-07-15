# Changelog

## Unreleased

## v0.3.6

- test(artifacts): make the metrics snapshot gate restore the committed summary bytes after exercising regeneration, so ordinary CTest runs cannot invalidate the later release reproducibility check.
- build(wheels): set the macOS universal2 deployment floor to 11.0, matching the documented availability of the shipped C++20 semaphore and jthread implementation.
- release: supersede v0.3.5 after its validation-pack lane exposed the tracked-artifact mutation; pricing behavior, Python 3.8 wheel support, and accepted Heston evidence are unchanged.

## v0.3.5

- build(wheels): pin cibuildwheel v3.4.1, the latest line that still builds the declared Python 3.8 surface; v4.x intentionally rejects Python 3.8 selectors, and restore the executable bit on the release reproduction entrypoint.
- release: supersede v0.3.4 after its wheel preflight exposed the action/support mismatch; pricing behavior, the manylinux_2_28 compiler baseline, and accepted Heston evidence are unchanged.

## v0.3.4

- build(wheels): move the Linux wheel baseline from manylinux2014/GCC 10 to manylinux_2_28 x86_64 so the shipped C++20 `std::counting_semaphore` implementation compiles against a conforming libstdc++; refresh cibuildwheel to v4.1.0.
- test(python): replace a sub-50 ms shared-runner timing assertion with a 512-row threaded-path parity contract; performance claims remain bound to the frozen benchmark artifacts rather than noisy CI wall-clock samples.
- build(release): validate the committed metrics snapshot before artifact regeneration, then exclude that commit-binding guard from the post-generation FAST replay; the regenerated summary still hard-fails on missing or malformed required artifacts.
- release: supersede v0.3.3 after its platform-wheel lane exposed the legacy compiler mismatch; pricing behavior and accepted Heston evidence are unchanged.

- docs(portfolio): reorganize the public README around the pricing surface, C++/Python quickstarts, architecture, frozen validation evidence, reproducibility, and explicit release boundaries
- docs(heston): add a provenance note for the verified next-release calibration-grid candidate and its bounded 14.2x compact-input measurement
- feat(protocol): freeze synthetic validation grid + tolerances; headline scripts now require `--scenario-grid` + `--tolerances` and record protocol hashes in the manifest/metrics snapshot
- feat(heston,mc): Andersen QE variance paths, deterministic counter RNG, CLI/pybind confidence intervals for MC Greeks
- ops(gpt-bundle): hard-gate empty run logs and include base commit diffs + commit lists in GPT bundles
- ops(gpt-bundle): fail on empty commit ranges unless `--allow-empty-diff`, and prefer merge-parent base on main merge commits
- ops(artifacts): default script output paths now point at `docs/artifacts/` to keep manifest entries canonical
- ops(artifacts): reproduce_all now builds full QL parity/bench/WRDS sample evidence before metrics snapshot, and metrics generation hard-fails when required artifacts are missing; validation pack is emitted at the end of the run
- ops(artifacts): enforce canonical manifest usage in metrics summaries and add a FAST guard against `artifacts/` writes (tests now emit to temp outputs)
- ops(artifacts): allow `QUANT_MANIFEST_PATH` overrides and scrub absolute external paths from the canonical manifest
- ops(artifacts): preserve metrics summary `generated_at` when the content is unchanged for stable CURRENT_RESULTS sync
- test(artifacts): isolate protocol/config guard runs to temp manifests and fail if canonical manifest contains absolute paths outside the repo
- ops(data-policy): enforce `# SYNTHETIC_DATA` markers for sample CSVs, regenerate synthetic WRDS sample data, and skip comment lines in sample loading
- dev(test): add `requirements-dev.txt` and document test dependencies (matplotlib included)
- wrds(cache): add WRDS parquet cache support and a bulk cache builder script for real-data slices
- wrds(local): document local WRDS OptionMetrics parquet stash and include a manifest in the validation bundle
- wrds(local): require explicit WRDS_LOCAL_ROOT / dateset config for local mode, keep sample artifacts as default, and scrub repo-relative paths in committed artifacts
- wrds(validity): hard-fail as-of correctness checks for calibration/OOS and add poison FAST coverage (with `WRDS_SAMPLE_PATH` override)
- wrds(panel): make `wrds_pipeline_dates_panel.yaml` the canonical panel config and log `panel_id` in WRDS provenance
- wrds(panel): require `panel_id` in dateset configs (no legacy `dataset_id`) and record data mode + date ranges in WRDS provenance
- docs(project_state): refresh project_state docs and generated indices

## v0.3.3

- feat(heston,python): add native and Python `heston_put_analytic` pricing plus `heston_calls_analytic_batch(markets, params)` and `heston_puts_analytic_batch(markets, params)` for contiguous `(n, 5)` matrices; scalar and batch puts share discounted put-call parity, with elementwise scalar parity and fail-closed input validation, and the installed module exposes native-derived `__version__` metadata.
- feat(heston,python): add broadcast batch price/implied-volatility metrics and `heston_call_metrics_grid`, returning a contiguous candidate-major `(p,m,2)` grid from compact market and parameter matrices with overflow-before-allocation guards.
- perf(python,heston): bound analytic batch execution to a process-wide four-worker budget with one worker per 32 rows; concurrent callers share the same cap and small batches stay on the caller thread.
- test(python): run one shared installed-wheel contract across cibuildwheel and pull-request CI, covering scalar analytics, batch parity, concurrency determinism, documented validation, and the quickstart.
- build(release): build and validate one source distribution, rebuild and install a wheel from it, keep internal Project OS/run material out of the archive, and merge collision-free platform wheel artifacts under one guarded TestPyPI publisher.
- build(provenance): validate the complete downloaded release set with Twine and emit a separate deterministic manifest binding artifact hashes, version, source commit, and tested runtime before any guarded upload. This is local/CI release-candidate evidence only; PyPI and TestPyPI availability are not asserted.

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

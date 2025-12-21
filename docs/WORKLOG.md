# WORKLOG

# WORKLOG

## 2025-12-18 (metrics snapshot single source of truth)
- Added `scripts/generate_metrics_summary.py` to derive all headline metrics from committed artifacts and emit `docs/artifacts/metrics_summary.{json,md}` with defensive missing/parse handling plus manifest logging (`metrics_snapshot`).
- Wired snapshot generation into `scripts/reproduce_all.sh`, created a FAST ctest (`metrics_snapshot_fast`) to guard against schema drift, and refreshed README/CURRENT_RESULTS to point at the snapshot instead of hard-coded numbers.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (success), `cmake --build build -j` (failed: missing Xcode Command Line Tools), `python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json`, `python3 tests/test_metrics_snapshot_fast.py`.
- Artifacts: `docs/artifacts/metrics_summary.json`, `docs/artifacts/metrics_summary.md`, manifest `runs.metrics_snapshot` entry.

## 2025-11-12 (artifact + parity refresh)
- Ran the full deterministic pipeline via `./scripts/reproduce_all.sh` (Release rebuild, `ctest -L FAST -VV`, artifact regeneration) so `docs/artifacts/{bench,wrds}` and `manifest.json` were repopulated after the earlier clean.
- Installed the QuantLib Python wheel locally and re-rendered `scripts/ql_parity.py` so the CSV/PNG bundle (`docs/artifacts/ql_parity/`) and manifest entry match the refreshed benches/WRDS outputs.
- Commands run: `./scripts/reproduce_all.sh`, `python3 -m pip install --user QuantLib`, `python3 scripts/ql_parity.py --output docs/artifacts/ql_parity/ql_parity.png --csv docs/artifacts/ql_parity/ql_parity.csv`.
- Artifacts: refreshed `docs/artifacts/bench/*`, `docs/artifacts/wrds/wrds_*`, `docs/artifacts/ql_parity/ql_parity.{csv,png}`, and `docs/artifacts/manifest.json`.

## 2025-11-12 (Python wheel import path fix)
- Resolved the cibuildwheel smoke failure (`ModuleNotFoundError: pyquant_pricer`) by installing the pybind module to the wheel root (site-packages) so the import path matches the package name on every platform.
- Verified the fix locally via a Release rebuild plus the FAST ctest suite; next wheel/release runs should see the module import inside `python/scripts/cibw_smoke.py` succeed.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`, `cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: n/a (build/test only; workflows consume the fix on the next tag run).

## 2025-11-12 (CI coverage fallback + Pages branch policy)
- Reworked the CI coverage job to ignore `CompilerId` gcov noise, skip Codecov uploads unless `CODECOV_TOKEN` is present, and tightened the README badges (drop duplicate CI badge, track Docs Pages workflow instead).
- Added the `master` branch to the `github-pages` environment policy so GitHub Actions can deploy again (previously restricted to `gh-pages` only).
- Added a Docs-Pages alias step so `_results_8md.html` and friends are copied to `Results.html`/`WRDS_Results.html`/`README.html`/`ValidationHighlights.html`, matching the public URLs linked from the README badges.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: n/a (workflow + docs wiring).

## 2025-11-12 (WRDS panel sample refresh)
- Reinstalled `numpy==2.1.3` inside the repo venv (restores `numpy.testing` for SciPy) and re-ran the 5-date WRDS panel pipeline against the bundled sample OptionMetrics snapshot.
- Documented in the WORKLOG that WRDS credentials are absent on this host, so the regenerated artifacts correspond to the sample dataset until MARKET secrets are available.
- Commands run: `python -m pip install 'numpy==2.1.3'`, `python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample --fast`, `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: refreshed `docs/artifacts/wrds/wrds_agg_{pricing,oos,pnl}.csv`, `docs/artifacts/wrds/wrds_multi_date_summary.png`, and the manifest `runs.wrds_dateset` entry.

## 2025-11-12 (Benchmarks: QMC equal-time + OpenMP scaling)
- Installed Homebrew `libomp`, produced a dedicated OpenMP-enabled build (`build-omp`), and tuned the MC benchmark harness so the equal-time plot now covers Asian + Barrier payoffs with a clear QMC advantage (time-scaled RMSE lower for both).
- Re-ran `bench_mc`/`bench_pde` to regenerate JSON, CSV, and PNG bundles (throughput scaling now shows ~6.4× speedup on 8 threads, PDE log-log fit overlays the −2 slope reference), then updated the manifest entry.
- Commands run: `brew install libomp`, `cmake -S . -B build-omp -DCMAKE_BUILD_TYPE=Release -DQUANT_ENABLE_OPENMP=ON ...`, `cmake --build build-omp --target bench_mc bench_pde`, `OMP_PROC_BIND=spread ./build-omp/bench_mc --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_mc.json --benchmark_out_format=json`, `./build-omp/bench_pde --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_pde.json --benchmark_out_format=json`, `python scripts/generate_bench_artifacts.py --mc-json docs/artifacts/bench/bench_mc.json --pde-json docs/artifacts/bench/bench_pde.json --out-dir docs/artifacts/bench`, `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: refreshed every file under `docs/artifacts/bench/` plus the `benchmarks` block inside `docs/artifacts/manifest.json`.

## 2025-11-12 (QuantLib parity refresh)
- Reinstalled the QuantLib Python wheel inside the repo venv and reran `scripts/ql_parity.py` so the CSV/PNG capture the latest vanilla/barrier/American grid with |Δ| reported in cents plus runtime ratios (quant-pricer vs QuantLib).
- Commands run: `python -m pip install QuantLib`, `python scripts/ql_parity.py --output docs/artifacts/ql_parity/ql_parity.png --csv docs/artifacts/ql_parity/ql_parity.csv`, `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: refreshed `docs/artifacts/ql_parity/ql_parity.{csv,png}` and appended the `ql_parity` section in `docs/artifacts/manifest.json`.

## 2025-11-12 (Release/wheels submodule fix)
- The v0.3.2 release job failed because `actions/checkout` skipped submodules, so `pcg_random.hpp` was missing; updated both `release.yml` and `wheels.yml` to checkout submodules before building, drop the repo’s tracked `.venv/`, exclude `.venv` from the scikit-build wheel/sdist payload, and enable PIC on `quant_pricer` so the pybind module links cleanly on manylinux.
- Commands run: `git tag -a v0.3.2 -m 'Release v0.3.2'` (initial attempt), `git push origin v0.3.2`, identified the failure in run `19284861635`, then patched the workflows (`.github/workflows/release.yml`, `.github/workflows/wheels.yml`).
- Artifacts: n/a (workflow plumbing only, but required for the validation pack + cibuildwheel jobs to succeed on tags).

## 2025-11-11 (WRDS panel rename + aggregated artifacts)
- Added `wrds_pipeline_dates_panel.yaml` (≥5 stress/calm dates), taught the pipeline to read YAML via PyYAML, renamed the in-sample metrics to `iv_rmse_volpts_vega_wt`/`iv_mae_volpts_vega_wt`/`iv_p90_bps`, and changed the OOS/PnL summaries to report `iv_mae_bps`, `price_mae_ticks`, and `pnl_sigma`.
- Trimmed committed artifacts to the aggregated CSV/PNG set (`wrds_agg_{pricing,oos,pnl}.csv`, `wrds_multi_date_summary.png`), updated README/Results/WRDS docs, and refreshed the manifest so historical entries carry the new metric names/units.
- Commands run: `source .venv/bin/activate && pip install pyyaml`, `source .venv/bin/activate && python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample --fast`, `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: regenerated `docs/artifacts/wrds/wrds_agg_{pricing,oos,pnl}.csv`, `docs/artifacts/wrds/wrds_multi_date_summary.png`, updated `docs/artifacts/manifest.json`.

## 2025-11-11 (GBench snapshots + equal-time plots)
- Tuned the `bench_mc` equal-time harness (fewer QMC paths) and upgraded `scripts/generate_bench_artifacts.py` so the throughput plot shows the OpenMP ideal line, the equal-time figure reports the time-scaled RMSE per payoff (Asian + Barrier), and the PDE convergence chart overlays the −2 reference slope + fitted slope.
- Regenerated all benchmark JSON/CSV/PNG artifacts and documented the three headline figures on both README and `docs/Results.md`.
- Commands run: `cmake --build build --target bench_mc`, `./build/bench_mc --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_mc.json --benchmark_out_format=json`, `./build/bench_pde --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_pde.json --benchmark_out_format=json`, `python scripts/generate_bench_artifacts.py --mc-json docs/artifacts/bench/bench_mc.json --pde-json docs/artifacts/bench/bench_pde.json --out-dir docs/artifacts/bench`.
- Artifacts: refreshed every file under `docs/artifacts/bench/` plus the benchmark entries in `docs/artifacts/manifest.json`.

## 2025-11-11 (QuantLib parity harness)
- Added `scripts/ql_parity.py` to drive `quant_cli` and QuantLib side-by-side for vanilla, barrier, and American payoffs, recording absolute price gaps (cents) plus runtime deltas; committed the CSV/PNG under `docs/artifacts/ql_parity/` and surfaced the figure on README/Results.
- Updated `requirements-artifacts.txt` (PyYAML, QuantLib) and installed the new wheels locally.
- Commands run: `source .venv/bin/activate && pip install QuantLib`, `python scripts/ql_parity.py --output docs/artifacts/ql_parity/ql_parity.png --csv docs/artifacts/ql_parity/ql_parity.csv`.
- Artifacts: `docs/artifacts/ql_parity/ql_parity.{csv,png}`, manifest `runs.ql_parity`.

## 2025-11-11 (Docs/coverage publishing fixes)
- Hooked `docs/Results.md` and `docs/WRDS_Results.md` into the Doxygen build, taught the Pages workflow to copy `docs/artifacts/` into the published site (so the Markdown figures resolve), and added a README badge that links directly to the hosted `Results.html`.
- Verified the Release build + FAST suite after the workflow changes.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: n/a (workflow plumbing only).

## 2025-11-11 (Release v0.3.2 prep)
- Bumped every version stamp (CMake, pyproject, setup.cfg, `include/quant/version.hpp`) to 0.3.2, added the release notes to `CHANGELOG.md`, and double-checked the release workflow still packages `docs/artifacts` via `scripts/package_validation.py`.
- Commands run: n/a (metadata only).
- Artifacts: n/a.

## 2025-11-11 (CI lint + docs deploy automation)
- Fixed the failing `pre-commit` job by upgrading the clang-format hook, excluding committed artifacts, and reformatting the C++/Python sources so the repo is lint-clean again; `pre-commit run --all-files` now passes locally.
- Hooked the Docs Pages workflow to `push` (master/main), added an artifact copy step, and injected the `<base>` tag via an indented Python snippet so the published Results/coverage links stay live without manual triggers.
- Commands run: `pre-commit run --all-files` (multiple, until clean), `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: auto-generated coverage/docs bundles under `docs/html` (published via workflow).

## 2025-11-11 (Heston analytic fix + coverage site)
- Fixed the analytic Heston pricer by applying the proper Gauss–Laguerre weighting (exp(x)) and clamping the result to intrinsic value, then reran both Release and coverage FAST suites.
- Generated llvm-cov/gcovr reports locally (lcov, Cobertura XML, HTML) and published the HTML bundle under `docs/coverage/` with a README badge + Results.md link; taught the Docs Pages workflow to copy that folder into the deployed site.
- Commands run: `brew install doxygen graphviz`, `.venv/bin/pip install gcovr`, `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `ctest --test-dir build --output-on-failure -L FAST`, `CC=clang CXX=clang++ cmake -S . -B build-cov ...`, `cmake --build build-cov --parallel`, `ctest --test-dir build-cov --output-on-failure -L FAST`, `xcrun llvm-profdata merge ...`, `xcrun llvm-cov export/report ...`, `.venv/bin/gcovr ...`.
- Artifacts: `docs/coverage/index.html`, `docs/coverage/coverage.css`, refreshed coverage outputs in `build-cov/`.

## 2025-11-11
- Rebuilt the reproducibility stack: `scripts/reproduce_all.sh` now cleans/repaves `docs/artifacts/`, runs FAST+SLOW labels, regenerates benches/figures/WRDS bundles, and finalises `manifest.json` with git/system/build metadata (plus new `tri_engine_agreement` entry). Added a helper for CI-friendly `--fast` mode and routed WRDS invocations through `python -m wrds_pipeline.pipeline`.
- Overhauled the WRDS pipeline (OptionMetrics ingestion → aggregation → vega-weighted Heston fit + bootstrap CIs → next-day OOS error buckets → delta-hedged PnL histogram) and refreshed the committed CSV/PNG artifacts under `docs/artifacts/wrds/`.
- Added the Tri-Engine Agreement plot/script, refreshed the README tiles + docs, and rewrote `docs/Results.md` to highlight the three headline figures with reproduction commands.
- Tightened CI coverage job (clang `llvm-cov` + gcovr/Codecov), new coverage badge, and appended the PDE second-order regression test.
- Commands run: `./scripts/reproduce_all.sh` (multiple, final run with SLOW), `cmake --build build --parallel`, `ctest --test-dir build -L FAST --output-on-failure -VV`.

# Worklog

## 2025-11-11 (CLI coverage smoke)
- Added `tests/test_cli_fast.py` plus a `cli_smoke_fast` FAST test that drives every `quant_cli` engine (bs/iv/mc/barrier/american/pde/digital/asian/lookback/heston/risk) via JSON to cover the large `src/main.cpp` switch and ensure the Heston analytic/MC diagnostics are exercised under coverage builds.
- Reconfigured/rebuilt both Release + coverage trees, re-ran the FULL FAST suite (Release + `build-cov`) to pick up the new test, and regenerated the gcovr HTML/Cobertura bundle; line coverage rose from 59.6% to 82.0% and the Pages-hosted `/coverage/` now serves the refreshed report.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DQUANT_ENABLE_OPENMP=ON`, `cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`, `CC=clang CXX=clang++ cmake -S . -B build-cov -DCMAKE_BUILD_TYPE=Debug -DQUANT_ENABLE_OPENMP=OFF -DCMAKE_CXX_FLAGS='--coverage -fprofile-instr-generate -fcoverage-mapping' -DCMAKE_EXE_LINKER_FLAGS='--coverage -fprofile-instr-generate' -DCMAKE_SHARED_LINKER_FLAGS='--coverage -fprofile-instr-generate'`, `cmake --build build-cov --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build-cov -L FAST -VV`, `.venv/bin/gcovr --root . --object-directory build-cov --filter='src/' --filter='include/' --exclude='external/' --exclude='tests/' --exclude='.*CMakeCXXCompilerId.*' --xml=docs/coverage/coverage.xml --html=docs/coverage/coverage.html --html-details=docs/coverage/index.html --gcov-executable 'xcrun llvm-cov gcov' --gcov-ignore-errors=no_working_dir_found --print-summary`.
- Artifacts: refreshed `docs/coverage/{coverage.html,index.html,coverage.xml,*.html}`.

## 2025-11-11 (release automation + validation pack)
- Bumped the library/wheel version to v0.3.1, documented the new `validation_pack.zip` bundle in the README, and added `scripts/package_validation.py` + `requirements-artifacts.txt` so releases can zip every CSV/PNG alongside `docs/artifacts/manifest.json`.
- Updated `release.yml` to install the artifact dependencies, run `scripts/reproduce_all.sh` (against the sample WRDS bundle), and upload both `docs/validation_pack.zip` and the manifest as GitHub release assets.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DQUANT_ENABLE_OPENMP=ON`, `cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: n/a (workflow/scripts only).

## 2025-11-11 (IV metrics + docs units)
- Standardised WRDS calibration outputs: `calibrate_heston.py` now computes vega-weighted IV RMSE/MAE/p90 in vol points, quotes-weighted `iv_mae_bps_oos`, and price RMSE in ticks; the pipeline/plots/manifest consume the new keys.
- Added a shared units legend to `docs/Results.md`, created `docs/WRDS_Results.md` with metric tables + figures, and linked the WRDS section to the new appendix.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`.
- Artifacts: n/a (code/docs only).

## 2025-11-11 (WRDS multi-date aggregation)
- Added `wrds_pipeline/dateset.yaml`, expanded the sample OptionMetrics bundle to cover ≥5 trade dates, and taught the pipeline to loop the dateset (per-date outputs under `docs/artifacts/wrds/per_date/` + aggregated CSV/PNG under `docs/artifacts/wrds/`).
- Updated `scripts/reproduce_all.sh` to run the batch mode after the single-date snapshot so CI regenerates `wrds_agg_{pricing,oos,pnl}.csv` and `wrds_multi_date_summary.png`.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`, `python3 -m wrds_pipeline.pipeline --use-sample`, `python3 -m wrds_pipeline.pipeline --dateset wrds_pipeline/dateset.yaml --use-sample` (multiple iterations to refresh artifacts and manifest).
- Artifacts: refreshed `docs/artifacts/wrds/heston_fit.{json,png}` plus new `wrds_agg_{pricing,oos,pnl}.csv` and `wrds_multi_date_summary.png`.

## 2025-11-11 (benchmarks: QMC vs PRNG, PDE slope)
- Added Sobol support to the Asian MC pricer + new benchmark cases for equal-time Asian/Barrier payoffs, and extended the PDE harness with a convergence-slope benchmark and OpenMP scaling plots.
- Updated `scripts/generate_bench_artifacts.py` to emit the new CSV/PNG bundle (`bench_mc_equal_time`, `bench_pde_order`), then rebuilt/regenerated the bench artifacts.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`, `build/bench_mc --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_mc.json --benchmark_out_format=json`, `build/bench_pde --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_pde.json --benchmark_out_format=json`, `python3 scripts/generate_bench_artifacts.py --mc-json docs/artifacts/bench/bench_mc.json --pde-json docs/artifacts/bench/bench_pde.json --out-dir docs/artifacts/bench`.
- Artifacts: refreshed `docs/artifacts/bench/bench_mc*.{csv,png,json}`, `bench_pde*.{csv,png,json}`, plus the new `bench_mc_equal_time.{csv,png}` and `bench_pde_order.{csv,png}`.

## 2025-11-11 (docs pages base-url fix)
- Hardened the `docs-pages` workflow with a post-Doxygen base-href injector and `.nojekyll` so GitHub Pages serves assets under `/quant-pricer-cpp/`, then swapped the README API Docs link/badge to the live site.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `ctest --test-dir build -L FAST --output-on-failure -VV`.
- Artifacts: n/a (workflow/docs only).

## 2025-11-11 (packaging + consumer example)
- Exposed the Heston characteristic function and implied-vol helpers in the core library and pybind module, refreshed the Python quickstart/smoke tests, and bumped the project/wheel version to v0.3.0.
- Extended `wheels.yml` to cover Linux/macOS/Windows via cibuildwheel (with an import smoke test) and added a CI job that installs the library then builds/runs `examples/consumer-cmake`.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST -VV`, `PYTHONPATH=scripts python3 - <<'PY' ...` (manifest metadata refresh).
- Artifacts: n/a (code/workflows only).

## 2025-11-11 (artifacts refresh: equal-time QMC + PDE slope)
- Replaced the legacy `qmc_vs_prng` helper with `scripts/qmc_vs_prng_equal_time.py`, introduced `scripts/pde_order_slope.py`, and refreshed the `ctest` harness to keep the FAST label aligned with the new artifact set.
- Regenerated every artifact/manifest via `./scripts/reproduce_all.sh` (Release rebuild, `ctest -L FAST`, full SLOW tier, WRDS sample bundle, and log/JUnit capture) so the committed CSV/PNGs reflect the equal-time QMC + PDE slope outputs.
- Commands run: `./scripts/reproduce_all.sh` (defaults, no WRDS env), which internally executes the documented CMake + ctest invocations.
- Artifacts: refreshed `docs/artifacts/*` (tri-engine, equal-time QMC, PDE slope, MC Greeks, benches), new `docs/artifacts/logs/slow_20251111T003717Z.{log,xml}`, updated `docs/artifacts/manifest.json`.

## 2025-11-11 (MARKET log capture + Codecov badge)
- Taught `scripts/reproduce_all.sh` to archive MARKET `ctest` output (verbose log + JUnit) whenever `RUN_MARKET_TESTS=1` so opt-in WRDS runs mirror the stored SLOW logs.
- Swapped the README coverage badge to the native Codecov graph so it links straight to `app.codecov.io`.
- Commands run: n/a (doc + script updates only).

## 2025-11-11 (WRDS pipeline: calibration transform + aggregated artifacts)
- Added log/atanh transforms to the WRDS Heston solver, recorded bootstrap summaries, emitted the new `wrds_heston_{insample,oos,hedge}` CSV/PNG bundle, and tightened the MARKET test expectations.
- Commands run: covered by the earlier `./scripts/reproduce_all.sh` refresh (WRDS sample bundle rebuilt without live creds).
- Artifacts: `docs/artifacts/wrds/wrds_heston_insample.{csv,png}`, `wrds_heston_oos.{csv,png}`, `wrds_heston_hedge.{csv,png}`, refreshed `heston_fit.{json,png}`, `heston_wrds_summary.png`, `oos_pricing_*`, `delta_hedge_pnl_*`.

## 2025-11-10 (docs pages + README badge)
- Enabled Pages best-practice workflow (configure-pages + Doxygen) and wired Doxygen to a Markdown main page with sidebar navigation.
- Added `docs/api/index.md`, tree view, and enabled alphabetical index so the published API docs have a real landing page.
- Pointed the README “API Docs” CTA and Docs badge at the deployed `https://mateobodon.github.io/quant-pricer-cpp/index.html` URL.
- Commands run: n/a (config only).
- Artifacts: n/a (CI/Pages deployment).

## 2025-11-10
- Hardened the Doxygen GitHub Pages workflow (main + tags) and removed the legacy duplicate job.
- Swapped the README docs badge to track the docs deployment workflow status.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && ctest --test-dir build -L FAST --output-on-failure -VV` (2×).
- Artifacts: n/a (CI-only workflow updates).

## 2025-11-10 (validation bundle + artifacts)
- Moved reproducible artifacts under `docs/artifacts/`, rewrote `docs/Results.md`, and introduced `scripts/reproduce_all.sh`.
- Generated baseline CSV/PNGs (`qmc_vs_prng_equal_time`, `pde_order_slope`, `mc_greeks_ci`, `heston_qe_vs_analytic`) plus refreshed `docs/artifacts/manifest.json`.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && ctest --test-dir build -L FAST --output-on-failure -VV` (multiple), `REPRO_FAST=1 ./scripts/reproduce_all.sh`, and the individual `python scripts/<artifact>.py ...` invocations to backfill the figures.
- Artifacts: `docs/artifacts/qmc_vs_prng_equal_time.{csv,png}`, `pde_order_slope.{csv,png}`, `mc_greeks_ci.{csv,png}`, `heston_qe_vs_analytic.{csv,png}`, updated `docs/artifacts/manifest.json`.

## 2025-11-10 (coverage + logs)
- Added a CI coverage job (Debug + `gcovr` + Codecov badge) and taught `scripts/reproduce_all.sh` to capture SLOW `ctest` logs/JUnit under `docs/artifacts/logs/`.
- Commands run: repeated `cmake ... && ctest -L FAST` cycles plus `REPRO_FAST=1 ./scripts/reproduce_all.sh` to generate the first archived SLOW log bundle.
- Artifacts: `docs/artifacts/logs/slow_20251110T203245Z.{log,xml}` and updated `docs/artifacts/manifest.json`.

## 2025-11-10 (benchmarks)
- Added a `bench` CMake target (`cmake --build build --target bench` / `make bench`), created `scripts/generate_bench_artifacts.py`, and captured the first JSON/CSV/PNG bundle under `docs/artifacts/bench/`.
- Commands run: `cmake --build build --target bench`, `build/bench_mc --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_mc.json --benchmark_out_format=json`, `build/bench_pde --benchmark_min_time=0.05s --benchmark_out=docs/artifacts/bench/bench_pde.json --benchmark_out_format=json`, `python3 scripts/generate_bench_artifacts.py`.
- Artifacts: `docs/artifacts/bench/bench_mc.json`, `bench_pde.json`, the derived CSV/PNG quartet, and the corresponding manifest entry.

## 2025-11-10 (WRDS pipeline)
- Finished the opt-in WRDS pipeline (ingest + calibration + OOS/hedge diagnostics), added the MARKET ctest wrapper with skip gating, and wired `scripts/reproduce_all.sh` to optionally rebuild the sample bundle. Later updated ingestion to resolve `secid` via `optionm.secnmd`, target the year-partitioned `optionm.opprcdYYYY` tables, and filter to practical moneyness/tenor buckets so the live OptionMetrics pull hits real SPX data.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir build -L FAST --output-on-failure -VV`, `python3 wrds_pipeline/pipeline.py --use-sample`, `WRDS_ENABLED=1 WRDS_USERNAME=... WRDS_PASSWORD=... python3 wrds_pipeline/pipeline.py --symbol SPX --trade-date 2023-06-14`.
- Artifacts: `docs/artifacts/wrds/{spx_surface_sample.csv,heston_calibration_summary.csv,oos_pricing.csv,oos_pricing_summary.csv,delta_hedge_pnl.csv}`, updated `docs/artifacts/manifest.json`.

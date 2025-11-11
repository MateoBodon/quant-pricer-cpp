# WORKLOG

# WORKLOG

## 2025-11-11
- Rebuilt the reproducibility stack: `scripts/reproduce_all.sh` now cleans/repaves `docs/artifacts/`, runs FAST+SLOW labels, regenerates benches/figures/WRDS bundles, and finalises `manifest.json` with git/system/build metadata (plus new `tri_engine_agreement` entry). Added a helper for CI-friendly `--fast` mode and routed WRDS invocations through `python -m wrds_pipeline.pipeline`.
- Overhauled the WRDS pipeline (OptionMetrics ingestion → aggregation → vega-weighted Heston fit + bootstrap CIs → next-day OOS error buckets → delta-hedged PnL histogram) and refreshed the committed CSV/PNG artifacts under `docs/artifacts/wrds/`.
- Added the Tri-Engine Agreement plot/script, refreshed the README tiles + docs, and rewrote `docs/Results.md` to highlight the three headline figures with reproduction commands.
- Tightened CI coverage job (clang `llvm-cov` + gcovr/Codecov), new coverage badge, and appended the PDE second-order regression test.
- Commands run: `./scripts/reproduce_all.sh` (multiple, final run with SLOW), `cmake --build build --parallel`, `ctest --test-dir build -L FAST --output-on-failure -VV`.

## 2025-11-11 (docs pages base-url fix)
- Hardened the `docs-pages` workflow with a post-Doxygen base-href injector and `.nojekyll` so GitHub Pages serves assets under `/quant-pricer-cpp/`, then swapped the README API Docs link/badge to the live site.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel`, `ctest --test-dir build -L FAST --output-on-failure -VV`.
- Artifacts: n/a (workflow/docs only).

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

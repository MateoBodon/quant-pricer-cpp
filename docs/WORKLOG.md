# WORKLOG

## 2025-11-10
- Hardened the Doxygen GitHub Pages workflow (main + tags) and removed the legacy duplicate job.
- Swapped the README docs badge to track the docs deployment workflow status.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && ctest --test-dir build -L FAST --output-on-failure -VV` (2×).
- Artifacts: n/a (CI-only workflow updates).

## 2025-11-10 (validation bundle + artifacts)
- Moved reproducible artifacts under `docs/artifacts/`, rewrote `docs/Results.md`, and introduced `scripts/reproduce_all.sh`.
- Generated baseline CSV/PNGs (`qmc_vs_prng`, `pde_convergence`, `mc_greeks_ci`, `heston_qe_vs_analytic`) plus refreshed `docs/artifacts/manifest.json`.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && ctest --test-dir build -L FAST --output-on-failure -VV` (multiple), `REPRO_FAST=1 ./scripts/reproduce_all.sh`, and the individual `python scripts/<artifact>.py ...` invocations to backfill the figures.
- Artifacts: `docs/artifacts/qmc_vs_prng.{csv,png}`, `pde_convergence.{csv,png}`, `mc_greeks_ci.{csv,png}`, `heston_qe_vs_analytic.{csv,png}`, updated `docs/artifacts/manifest.json`.

## 2025-11-10 (coverage + logs)
- Added a CI coverage job (Debug + `gcovr` + Codecov badge) and taught `scripts/reproduce_all.sh` to capture SLOW `ctest` logs/JUnit under `docs/artifacts/logs/`.
- Commands run: repeated `cmake ... && ctest -L FAST` cycles plus `REPRO_FAST=1 ./scripts/reproduce_all.sh` to generate the first archived SLOW log bundle.
- Artifacts: `docs/artifacts/logs/slow_20251110T203245Z.{log,xml}` and updated `docs/artifacts/manifest.json`.

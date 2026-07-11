---
generated_at: 2026-07-11T15:59:40.965347+00:00
git_sha: 0dbcd666288729bf519d4471e189685b623aba38
results_commit_sha: 0dbcd666288729bf519d4471e189685b623aba38
manifest_git_sha: 0dbcd666288729bf519d4471e189685b623aba38
branch: recovery/quant-pre-v3-20260710
commands:
  - python3 -m venv .venv
  - . .venv/bin/activate && python -m pip install -r requirements-dev.txt
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3
  - cmake --build build -j
  - PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure
  - PATH=$PWD/.venv/bin:$PATH REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2026-07-11T15:59:40.965347+00:00**).
Results commit SHA: `0dbcd666288729bf519d4471e189685b623aba38`.
Manifest git SHA recorded in snapshot: `0dbcd666288729bf519d4471e189685b623aba38` (code SHA captured in `docs/artifacts/manifest.json` at snapshot time).

Status overview (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok (sample bundle regression harness)

## Highlight metrics (from snapshot)
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=4.76346 (asian median=3.06425; call median=6.46267).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents, median=0.798752 cents, p95=0.855300 cents.
- Benchmarks: MC paths/sec (1t)=1.27500e+07, eff@max=0.953402.
- WRDS: median iv_rmse=0.00120828 (sample bundle regression harness).
- WRDS calibration claim gate: diagnostic-only; 5/5 sample fits converged,
  5/5 hit at least one exact parameter bound, and 0/5 are promotion eligible.
- WRDS hedge diagnostics: market-IV Black-Scholes-delta median PnL sigma
  `239.069` ticks; calibrated-Heston-delta median PnL sigma `249.249` ticks.
- WRDS Heston-delta numerical gate: 50/50 sample surface rows valid and 0
  invalid; the real five-date replay is separately fail-closed and is not
  represented by this sample result.

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- This update refreshed the sample metrics snapshot with explicit model-specific
  hedge attribution plus fail-closed calibration and Heston-delta numerical
  diagnostics.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

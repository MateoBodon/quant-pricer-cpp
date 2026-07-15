---
generated_at: 2026-01-25T21:13:43.226947+00:00
git_sha: 653b9e8e07364e5c682dabed5bae856a850c1136
results_commit_sha: 653b9e8e07364e5c682dabed5bae856a850c1136
manifest_git_sha: 653b9e8e07364e5c682dabed5bae856a850c1136
branch: codex/ticket-09-refresh-metrics-ax162s
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
Source: `docs/artifacts/metrics_summary.md` (generated at **2026-01-25T21:13:43.226947+00:00**).
Results commit SHA: `653b9e8e07364e5c682dabed5bae856a850c1136`.
Manifest git SHA recorded in snapshot: `653b9e8e07364e5c682dabed5bae856a850c1136` (code SHA captured in `docs/artifacts/manifest.json` at snapshot time).

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

## Vectorized portfolio risk and exact stress (v0.4.0)

The library now exposes a public C++ and installed Python Black-Scholes
portfolio engine:

- `bs_portfolio_risk` returns position price/value/Greeks plus
  quantity-weighted portfolio totals from a contiguous `(n,8)` matrix;
- `bs_portfolio_scenarios` exact-reprices five-factor scenario shocks and avoids
  the dense scenario-by-position matrix in aggregate-only mode;
- 60 mixed call/put QuantLib cases and 72 scenario cells passed the frozen
  independent evaluator. Worst absolute price error was `3.91e-14`, worst
  Greek error was `3.40e-12`, and worst portfolio scenario P&L error was
  `2.66e-13`;
- the final installed-wheel benchmark on Apple M3 Pro measured `20.18x` risk
  and `27.92x` scenario speedups, `20.25M` positions/s and `32.13M` cells/s;
- exact v0.4.0 wheel and source-distribution hashes, installed smoke, sanitizer,
  regression, resource, and limitation evidence are linked from
  `docs/product/DERIVATIVES_SYSTEM_HUB.md`.

These are deterministic Black-Scholes valuation/stress claims only. They do not
support a forecast, market-risk model, hedge, P&L, return, or trading claim.

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- Real-data SSVI temporal confirmation: `docs/artifacts/ssvi_temporal_holdout_v1_summary.json`.
- Native C++ SSVI benchmark: `docs/artifacts/ssvi_cpp_benchmark_v1.json`.
- Aggregate OptionMetrics SSVI robustness canary: `docs/artifacts/optionmetrics_ssvi_robustness_canary_v1.json`.
- Multi-date aggregate OptionMetrics SSVI robustness: `docs/artifacts/optionmetrics_ssvi_multidate_robustness_v1.json`.
- SSVI calibration-stability monitor status: `docs/artifacts/ssvi_calibration_stability_status_v1.json`.
- Portfolio-risk product hub: `docs/product/DERIVATIVES_SYSTEM_HUB.md`.
- Independent portfolio/QuantLib parity: `docs/artifacts/portfolio_risk_quantlib_parity_v1.json`.
- Installed-wheel performance/resource receipt: `docs/artifacts/portfolio_risk_benchmark_v1.json`.
- v0.4.0 wheel/sdist release receipt: `docs/artifacts/portfolio_risk_release_v040.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- This update refreshed the metrics snapshot; artifact blocks remain from the latest committed sample bundle run.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

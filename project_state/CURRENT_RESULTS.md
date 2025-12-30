---
generated_at: 2025-12-30T02:50:31Z
git_sha: 21eeba68923846a4c6015f697b741f4f22ef0f25
branch: main
commands:
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  - cmake --build build -j
  - ctest --test-dir build -L FAST --output-on-failure
  - python3 scripts/ql_parity.py --scenario-grid configs/scenario_grids/synthetic_validation_v1.json --tolerances configs/tolerances/synthetic_validation_v1.json --fast
  - python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-29T17:49:04.557055+00:00**).
Manifest git SHA recorded in snapshot: `21eeba68923846a4c6015f697b741f4f22ef0f25` (code SHA captured in `docs/artifacts/manifest.json` at snapshot time).

Status overview (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok (sample bundle regression harness)

## Highlight metrics (from snapshot)
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=4.17311 (asian median=1.5918; call median=6.75442).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents, median=0.798752 cents, p95=0.855300 cents.
- Benchmarks: MC paths/sec (1t)=9.77574e+06, eff@max=0.118153.
- WRDS: median iv_rmse=0.00120828 (sample bundle regression harness).

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- This update regenerated the QL parity artifacts (fast protocol grid) and refreshed the metrics snapshot; other artifact blocks remain from the latest committed sample bundle run.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

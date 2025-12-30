---
generated_at: 2025-12-30T11:10:31.082595+00:00
git_sha: 8b260859ab74faf2aff148493780e25281c9ce29
branch: codex/ticket-01_unify-artifacts-root
commands:
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  - cmake --build build -j
  - ctest --test-dir build -L FAST --output-on-failure
  - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
  - WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-30T11:10:31.082595+00:00**).
Manifest git SHA recorded in snapshot: `8b260859ab74faf2aff148493780e25281c9ce29` (code SHA captured in `docs/artifacts/manifest.json` at snapshot time).

Status overview (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok (sample bundle regression harness)

## Highlight metrics (from snapshot)
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=5.50480 (asian median=3.19824; call median=7.81137).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents, median=0.798752 cents, p95=0.855300 cents.
- Benchmarks: MC paths/sec (1t)=1.26987e+07, eff@max=0.127424.
- WRDS: median iv_rmse=0.00120828 (sample bundle regression harness).

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- This update refreshed the metrics snapshot; artifact blocks remain from the latest committed sample bundle run.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

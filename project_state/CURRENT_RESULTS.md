---
generated_at: 2025-12-26T09:34:49Z
git_sha: 9e4006eb8bb02ff21faaccaf1ebef41c36914e4c
branch: codex/ticket-05-ql-parity-grid-summary
commands:
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  - cmake --build build -j
  - ctest --test-dir build -L FAST --output-on-failure
  - python3 scripts/ql_parity.py --scenario-grid configs/scenario_grids/synthetic_validation_v1.json --tolerances configs/tolerances/synthetic_validation_v1.json
  - python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
  - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-26T09:29:16.141370+00:00**).
Manifest git SHA recorded in snapshot: `9e4006eb8bb02ff21faaccaf1ebef41c36914e4c`.

Status overview (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok (sample bundle regression harness)

## Highlight metrics (from snapshot)
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=4.77797 (asian median=3.41967; call median=6.13626).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents, median=0.798752 cents, p95=0.855300 cents.
- Benchmarks: MC paths/sec (1t)=1.36844e+07, eff@max=0.112353.
- WRDS: median iv_rmse=0.00120828 (sample bundle regression harness).

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- Artifacts refreshed via `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`; values above reflect the sample bundle regeneration.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

---
generated_at: 2025-12-23T22:30:27Z
git_sha: eb8b83464526fd2f5a4a82dcfc044d488cfb1c9c
branch: codex/ticket-03b-current-results-sync
commands:
  - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
  - WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
  - python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-23T22:28:29.174703+00:00**).
Manifest git SHA recorded in snapshot: `eb8b83464526fd2f5a4a82dcfc044d488cfb1c9c`.

Status overview (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok (sample bundle regression harness)

## Highlight metrics (from snapshot)
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=5.41126 (asian median=2.71457; call median=8.10794).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents.
- Benchmarks: MC paths/sec (1t)=1.11734e+07, eff@max=0.146101.
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

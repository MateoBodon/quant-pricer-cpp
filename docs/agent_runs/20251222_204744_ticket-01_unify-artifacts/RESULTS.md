# Results

- Canonicalized FAST test outputs: parity/greeks/Heston series tests now write to temp paths with `--skip-manifest`, and a new `artifacts_root_guard_fast` test fails if any files appear under `artifacts/`.
- Metrics snapshot generation now hard-requires the canonical manifest at `docs/artifacts/manifest.json`.
- Regenerated the sample bundle via `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`, updating `docs/artifacts/*`, `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.{md,json}`, and `docs/validation_pack.zip`.
- Verified no new files under `artifacts/` (`git status --porcelain artifacts` returned empty).
- Notes: reproduce_all emitted Heston MC diagnostic deviation warnings; OpenMP not enabled so `RngDeterminism.CounterRngThreadInvariant` was skipped; SLOW test logs were written to `docs/artifacts/logs/` (untracked).

Key metrics (from `docs/artifacts/metrics_summary.md`, generated 2025-12-22T21:02:46.901536+00:00):
- Tri-engine agreement: max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True.
- QMC vs PRNG: median RMSE ratio=7.41202 (asian median=2.62594; call median=12.1981).
- PDE order: slope=-2.0124, rmse_finest=0.00115728.
- QL parity: max diff=0.861583 cents.
- Benchmarks: MC paths/sec (1t)=1.30364e+07, eff@max=0.124117.
- WRDS: median iv_rmse=0.00120828 (sample bundle regression harness).

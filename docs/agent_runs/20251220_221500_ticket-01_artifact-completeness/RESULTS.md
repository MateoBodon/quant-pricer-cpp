# Results

- Root cause fixed: artifact generation now precedes FAST/SLOW tests and metrics snapshot, so QL parity, benchmarks, and WRDS sample evidence exist before validation.
- Metrics snapshot now hard-fails on missing/unreadable required artifacts using a single authoritative required-artifact registry (paths + required columns).
- Repro run refreshed artifacts under `docs/artifacts/` and produced `docs/validation_pack.zip`; metrics snapshot shows ql_parity/benchmarks/wrds = ok.
- Repo paths verified: benchmarks live under `docs/artifacts/bench/` and WRDS sample aggregates under `docs/artifacts/wrds/` (consistent with existing scripts).

## Artifact highlights
- QL parity: `docs/artifacts/ql_parity/ql_parity.csv`, `docs/artifacts/ql_parity/ql_parity.png`
- Benchmarks: `docs/artifacts/bench/` (bench_mc_paths.csv, bench_mc_equal_time.csv, plots)
- WRDS sample aggregates: `docs/artifacts/wrds/wrds_agg_pricing.csv`, `docs/artifacts/wrds/wrds_agg_oos.csv`, `docs/artifacts/wrds/wrds_agg_pnl.csv` (+ comparison plots)
- Metrics snapshot: `docs/artifacts/metrics_summary.md`, `docs/artifacts/metrics_summary.json`
- Manifest + validation pack: `docs/artifacts/manifest.json`, `docs/validation_pack.zip`

## Before/after
- Before (last snapshot 2025-12-18): ql_parity = missing, benchmarks = missing, wrds = missing.
- After (snapshot 2025-12-20): ql_parity = ok, benchmarks = ok, wrds = ok.

## Sources consulted
- None.

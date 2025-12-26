# Results

- Implemented QuantLib parity grid summary outputs: `docs/artifacts/ql_parity/ql_parity.csv` now includes bucket columns (`tenor_bucket`, `moneyness_bucket`, `vol_bucket`) plus per-row `abs_diff`/`rel_diff`, and the script emits `docs/artifacts/ql_parity/ql_parity_bucket_summary.csv` (count/max/median/p95) and `docs/artifacts/ql_parity/ql_parity_error_dist.png`.
- Metrics summary updated to report full-grid max/median/p95 for QuantLib parity and to require bucket columns in the parity CSV.
- Latest QuantLib parity metrics (from `docs/artifacts/metrics_summary.json` generated at 2025-12-26T09:29:16.141370+00:00):
  - max_abs_diff_cents_overall=0.861583
  - median_abs_diff_cents_overall=0.798752
  - p95_abs_diff_cents_overall=0.855300
- Headline snapshot highlights (same source):
  - QMC vs PRNG median RMSE ratio=4.77797 (asian=3.41967; call=6.13626)
  - Benchmarks MC paths/sec (1t)=1.36844e+07, eff@max=0.112353
  - WRDS median iv_rmse=0.00120828 (sample bundle)

Artifacts updated (post reproduce_all):
- `docs/artifacts/ql_parity/ql_parity.csv`
- `docs/artifacts/ql_parity/ql_parity_bucket_summary.csv`
- `docs/artifacts/ql_parity/ql_parity_error_dist.png`
- `docs/artifacts/ql_parity/ql_parity.png`
- `docs/artifacts/metrics_summary.json`
- `docs/artifacts/metrics_summary.md`
- `docs/artifacts/manifest.json`
- `docs/artifacts/bench/*`
- `docs/artifacts/qmc_vs_prng_equal_time.*`
- `docs/validation_pack.zip`

Notes:
- Initial FAST test runs failed due to outdated parity CSV and CURRENT_RESULTS mismatch; fixed by regenerating artifacts and updating `project_state/CURRENT_RESULTS.md`.
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` completed successfully (FAST + SLOW tests; MARKET skipped by default).

Bundle:
- `docs/gpt_bundles/20251226T094313Z_ticket-05_20251226_HHMMSS_ticket-05_ql-parity-grid-summary.zip`

# Results

- Enforced explicit-only WRDS local mode: local reads require `WRDS_LOCAL_ROOT` or `wrds_local_root` (dateset config); sample mode respects `WRDS_USE_SAMPLE=1`, and pipeline logs now report `source_today/source_next` per run.
- Local runs now default to `docs/artifacts/wrds_local/` (leaving `docs/artifacts/wrds/` as the sample bundle) and docs were updated to reflect explicit local behavior.
- Regenerated sample-mode artifacts with `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`, then refreshed `docs/artifacts/metrics_summary.*`, `docs/artifacts/manifest.json`, and `docs/validation_pack.zip`.
- Scrubbed repo artifacts to be repo-relative (no `/Users/...` paths) and documented the redistribution-risk note in `project_state/KNOWN_ISSUES.md`.
- Updated `project_state/CONFIG_REFERENCE.md`, `project_state/CURRENT_RESULTS.md`, `PROGRESS.md`, and `CHANGELOG.md` to reflect Ticket-06 changes.

Key metrics (from `docs/artifacts/metrics_summary.json`, generated at 2025-12-21T20:29:56.983890+00:00):
- tri_engine_agreement: max_abs_error_mc=0.00754518, max_abs_error_pde=0.00058701, mc_ci_covers_bs=True
- qmc_vs_prng_equal_time: rmse_ratio_overall_median=6.34988
- pde_order: slope=-2.01240, r2=0.999997, rmse_finest=0.00115728
- ql_parity: max_abs_diff_cents_overall=0.861583
- benchmarks: paths_per_sec_1t=12364148.91, efficiency_max_threads=0.118956
- wrds (sample bundle regression harness): median_iv_rmse_volpts_vega_wt=0.0160071, median_iv_mae_bps=136.233

Artifacts:
- Metrics snapshot: `docs/artifacts/metrics_summary.md`, `docs/artifacts/metrics_summary.json`
- Manifest: `docs/artifacts/manifest.json`
- WRDS sample bundle: `docs/artifacts/wrds/`
- Validation pack: `docs/validation_pack.zip`

Bundle:
- `docs/gpt_bundles/20251221T204414Z_ticket-06_20251221_202201_ticket-06_wrds-local-guardrails.zip`

Human merge checklist:
- No raw data or secrets committed
- Sample-mode reproduce_all passes
- FAST tests pass
- metrics_summary shows “sample bundle” and has no absolute paths
- Docs updated (PROGRESS + project_state as needed)

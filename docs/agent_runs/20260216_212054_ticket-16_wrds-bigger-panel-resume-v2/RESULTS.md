# Results

## Summary
- Added `wrds_pipeline_dates_panel_resume_v2.yaml` with a deterministic, pre-committed selection rule and `panel_id: wrds_panel_resume_v2`.
- Final panel size is 14 entries (>5), covering:
  - stress dates from v1 (`2020-03-16`, `2020-03-17`), and
  - Q1/Q3 first-trading-week anchors for each year 2020-2025.
- Ran the local parquet export workflow with fixed run id `wrds_local_resume_v2` and generated an aggregate-only resume snippet from the local metrics JSON.
- Local run provenance in `metrics_export_local.json`:
  - `machine_label`: `codex-worker`
  - `git_sha`: `fbf634a04e6787ace2022f32a2509520725f79d3`
  - `trade_date_range`: `2020-01-06` to `2025-07-01`
  - `next_trade_date_range`: `2020-01-07` to `2025-07-02`

## Headline aggregate metrics (local export)
Source: `artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.json`

- Pricing medians:
  - `median_iv_rmse_volpts_vega_wt`: `0.04041145678935248`
  - `median_iv_mae_bps`: `144.4921300300125`
- Comparison medians:
  - `median_heston_iv_rmse_volpts`: `0.0012435598870221328`
  - `median_bs_iv_rmse_volpts`: `0.00371414922528936`
  - `median_delta_iv_rmse_volpts`: `-0.002470589338267227`

Derived metric (requested):
- Heston vs BS median IV RMSE improvement %
  - Formula: `(BS - Heston) / BS * 100`
  - Value: `(0.00371414922528936 - 0.0012435598870221328) / 0.00371414922528936 * 100 = 66.51831115037523%`

## Output locations
- Tracked config:
  - `wrds_pipeline_dates_panel_resume_v2.yaml`
- Run log:
  - `docs/agent_runs/20260216_212054_ticket-16_wrds-bigger-panel-resume-v2/`
- Local-only outputs:
  - `artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.json`
  - `artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.md`
  - `artifacts/_local/wrds_local/wrds_local_resume_v2/manifest_local.json`
  - `artifacts/_local/wrds_local/wrds_local_resume_v2/resume_snippet_wrds_local.md`

## Notes
- Sample smoke initially failed outside `.venv` due to missing `matplotlib`; rerun in `.venv` succeeded.
- An initial 26-entry panel attempt was intentionally stopped due to runtime risk; the final committed rule uses a moderate 14-entry panel while remaining deterministic and pre-committed.

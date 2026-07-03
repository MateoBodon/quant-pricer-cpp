# Results

## Summary
- Closed the ticket-16 FAIL items by tracking the run log, adding the missing ticket spec file, and replacing non-reproducible test placeholders with full executable commands.
- Implemented a resume-snippet workflow via `scripts/generate_wrds_resume_snippet.py` with sanitization guardrails and FAST coverage in `tests/test_wrds_resume_snippet_from_sample_export_fast.py`.
- Updated `docs/RUNBOOK.md` with sample/local commands for generating resume snippets from `metrics_export_{sample,local}.json`.
- Kept real-data outputs local-only under `artifacts/_local/wrds_local/` (no tracked bulk data committed).

## Ticket-16 local export evidence
Local parquet run output (already produced during this run):
- `artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/metrics_export_local.json`
- `artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/metrics_export_local.md`
- `artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/manifest_local.json`

Headline aggregate metrics recorded from `metrics_export_local.json`:
- `pricing.median_iv_rmse_volpts_vega_wt = 0.026382963917417367`
- `pricing.median_iv_mae_bps = 164.1930283165783`
- `comparison.median_heston_iv_rmse_volpts = 0.0012435598870221328`
- `comparison.median_bs_iv_rmse_volpts = 0.00371414922528936`
- `comparison.median_delta_iv_rmse_volpts = -0.002470589338267227`

## Resume snippet outputs (local-only)
- Sample snippet: `artifacts/_local/wrds_local/wrds_local_ci_snippet/resume_snippet_wrds_sample.md`
- Local snippet: `artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/resume_snippet_wrds_local.md`

Both snippets are aggregate-only bullets and passed sanitization checks (no `/srv/data/wrds`, no `.parquet`, no `.csv`, no row-level dumps).

## Additional notes
- Added missing ticket doc: `docs/tickets/ticket-16_wrds-local-parquet-metrics-resume-refresh.md`.
- FAST suite is green after replacing placeholder bullets in `docs/NOW.md` that were blocking `docs_sanity_fast`.

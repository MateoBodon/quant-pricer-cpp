# Results

- Required `panel_id` in WRDS dateset configs (legacy `dataset_id` now errors) and added `use_sample`/`data_mode` + date-range provenance to WRDS manifest entries and per-date summaries (`wrds_pipeline/pipeline.py`, `docs/artifacts/manifest.json`, `docs/artifacts/wrds/per_date/2024-06-14/heston_fit.json`).
- Updated docs to reflect the single canonical dateset config and the new provenance fields (`project_state/CONFIG_REFERENCE.md`, `project_state/KNOWN_ISSUES.md`, `PROGRESS.md`, `CHANGELOG.md`).
- Refreshed reproducible artifacts + validation pack via the official pipeline; canonical outputs live under `docs/artifacts/` and `docs/validation_pack.zip`.
- Removed the tracked non-canonical `artifacts/` directory to keep the repo aligned with the canonical artifacts root.

Evidence checks:
- `docs/artifacts/manifest.json` `runs.wrds_dateset[]` now includes `panel_id`, `dateset_inputs`, `use_sample`, `data_mode`, `trade_date_range`, `next_trade_date_range`.
- `docs/artifacts/wrds/per_date/2024-06-14/heston_fit.json` includes `panel_id`, `use_sample`, `data_mode`, and date ranges.

Artifacts updated:
- `docs/artifacts/manifest.json`
- `docs/artifacts/metrics_summary.json`
- `docs/artifacts/metrics_summary.md`
- `docs/validation_pack.zip`
- WRDS/bench/parity outputs under `docs/artifacts/`

Bundle:
- docs/gpt_bundles/20251229T110129Z_ticket-03_20251229_103451_ticket-03_wrds-panel-single-source.zip

# Ticket: ticket-10_wrds-local-realdata-metrics

## Goal
Export license-safe real-data WRDS metrics (local cache) for resume updates, with provenance, without committing raw data.

## Scope
- Add `scripts/wrds_realdata_metrics_export.py` to summarize WRDS aggregated outputs into sanitized JSON/MD.
- Ensure WRDS pipeline can write outputs to a gitignored `wrds_local` root (add `--output-root` usage if needed).
- Add `.gitignore` coverage if missing and a FAST test for the exporter.
- Update `docs/RUNBOOK.md` with AX162-S sample/local commands.

## Acceptance Criteria
- Exporter reads only aggregated WRDS CSVs (`wrds_agg_pricing/oos/pnl` + comparison) and outputs scalar summary metrics.
- Output includes provenance: `panel_id`, date range, git SHA, data_mode, machine label.
- Supports `--use-sample` and local parquet mode via `WRDS_LOCAL_ROOT=/srv/data/wrds`.
- Writes to `artifacts/_local/wrds_local/` and path is gitignored.
- FAST test validates schema and asserts no restricted field names appear in export.
- Runbook includes exact commands for sample and local runs.

## Plan
1. Add exporter script and schema for JSON/MD output (`scripts/wrds_realdata_metrics_export.py`).
2. Add FAST test to validate schema/restricted fields (`tests/test_wrds_realdata_export_fast.py`) and register in `CMakeLists.txt`.
3. Update `docs/RUNBOOK.md` with AX162-S sample/local commands.
4. Update repo memory (`PROGRESS.md`, `docs/DECISIONS.md` if needed) and generate GPT bundle.

## Notes
- No raw WRDS/OptionMetrics data should be read or committed.

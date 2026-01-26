# Tests

- None (no unit/integration tests run).
- Local data check: `python3 - <<'PY'` to call `ingest_sppx_surface.load_surface` for each panel date + next_trade_date; all returned source=local with non-zero rows.
- Real-data pipeline (local stash): `python3 -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --fast` (first attempt timed out at 120s; second attempt completed).
- Other (non-test): regenerated `docs/artifacts/metrics_summary.*` and created the GPT bundle via `make gpt-bundle`.

# Results

- Initial end-to-end command ran FAST tests successfully, but the final assertion failed because the exporter reported `data_mode=sample`.
- First rerun with `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds` still fell back to sample due to missing parquet engine (`pyarrow`/`fastparquet`).
- Installed `pyarrow`, created a local dateset clone with explicit `wrds_local_root=/srv/data/wrds/wrds`, and reran the local pipeline.
- Local pipeline completed with `source_today=local`/`source_next=local` for all dates and produced:
  - `docs/artifacts/wrds_local/wrds_local_20260126_040817/metrics_export_local.json`
  - `docs/artifacts/wrds_local/wrds_local_20260126_040817/metrics_export_local.md`
  - `docs/artifacts/wrds_local/wrds_local_20260126_040817/resume_snippet.md`
- Provenance confirms `data_mode=local`, panel id `wrds_panel_calm_stress_v1`, and trade date range `2020-03-16` → `2024-06-14`.
- Note: per the ticket, `WRDS_LOCAL_ROOT=/srv/data/wrds` was set, but the actual parquet root lives at `/srv/data/wrds/wrds` and had to be specified in the dateset clone to avoid sample fallback.
- GPT bundle: `docs/_bundles/gpt_bundle_20260126_032021_ticket-10b_generate-realdata-metrics-and-resume-snippet.zip`.
- Added `pyarrow` to `requirements-dev.txt` and clarified the WRDS local root path plus parquet dependency in `docs/RUNBOOK.md`.
- Re-ran the end-to-end FAST + local pipeline/export; outputs landed under `docs/artifacts/wrds_local/wrds_local_20260126_051959/metrics_export_local.json` and `docs/artifacts/wrds_local/wrds_local_20260126_051959/metrics_export_local.md`, with manifest changes reverted afterward.

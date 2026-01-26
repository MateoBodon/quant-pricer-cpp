# ticket-10b_generate-realdata-metrics-and-resume-snippet

## Goal
Run the WRDS pipeline on the real local parquet cache (`/srv/data/wrds`) and generate the best-available license-safe headline metrics plus a resume-ready snippet (without committing raw data).

## Scope
- No engine changes.
- Execute `wrds_pipeline` in local mode with `WRDS_LOCAL_ROOT=/srv/data/wrds` into `artifacts/_local/wrds_local/<run_id>`.
- Run `scripts/wrds_realdata_metrics_export.py` to produce `metrics_export_local.json`/`.md` with provenance.
- Write a short `resume_snippet.md` next to the export (gitignored).
- Add a run log that records commands but does NOT paste restricted/raw identifiers.

## Acceptance Criteria
- Pipeline runs using `WRDS_LOCAL_ROOT=/srv/data/wrds` and writes only aggregated artifacts under `artifacts/_local/wrds_local/<run_id>`.
- Exporter succeeds on that root and produces `metrics_export_local.json` and `metrics_export_local.md` with provenance (panel_id/date ranges/git sha/machine label/data_mode=local).
- A `resume_snippet.md` is generated from the exported metrics (headline bullets only).
- Git status shows no new tracked WRDS data and no changes to `docs/artifacts/wrds/*`.
- FAST tests still pass.

## Plan
1. Create run log scaffolding under `docs/agent_runs/<run_name>/` and record the ticket prompt/commands.
2. Run the provided end-to-end command (FAST tests + local WRDS pipeline + exporter + JSON check).
3. Generate `resume_snippet.md` from the exported metrics output and ensure it remains gitignored.
4. Update run log artifacts (`RESULTS.md`, `TESTS.md`, `META.json`) and append `PROGRESS.md`.
5. Produce the GPT bundle with the ticket id.

## Notes
- Avoid logging raw WRDS identifiers, symbols, or paths beyond the approved local root.
- Use `QUANT_MACHINE_LABEL=AX162-S` for provenance.

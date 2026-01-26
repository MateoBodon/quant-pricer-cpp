# Ticket: ticket-10b_finish_track_runlog_and_clean_manifest

## Goal
Finish ticket-10b by tracking the real-data run log + dateset clone, staging PROGRESS/DECISIONS updates, and keeping the repo clean (no committed manifest churn) while preserving gitignored local metrics exports.

## Scope
- Track `docs/agent_runs/20260126_040139_ticket-10b_generate-realdata-metrics/*` (including `wrds_pipeline_dates_panel_local.yaml`).
- Track `docs/tickets/ticket-10b_generate-realdata-metrics-and-resume-snippet.md`.
- Update `docs/RUNBOOK.md` with correct WRDS local root guidance (AX162-S + worker_default whitelist) and the `pyarrow` dependency.
- Revert any `docs/artifacts/manifest.json` churn from local runs; do not touch `docs/artifacts/wrds/*`.
- Append ticket-10b completion notes to `PROGRESS.md` and `docs/DECISIONS.md`.
- Re-run FAST tests + local WRDS pipeline/export (per provided command), leaving outputs under `artifacts/_local/wrds_local/` (gitignored).

## Acceptance Criteria
- Run log folder is tracked and contains `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json` (no restricted identifiers).
- Ticket file for ticket-10b generation is tracked.
- `PROGRESS.md` + `docs/DECISIONS.md` include ticket-10b finish entries.
- `docs/RUNBOOK.md` documents `WRDS_LOCAL_ROOT` for AX162-S and worker_default, mentions `/srv/data/wrds` whitelist + nested `/srv/data/wrds/wrds`, and calls out `pyarrow`.
- `docs/artifacts/manifest.json` has no diff after finishing; `docs/artifacts/wrds/*` unchanged.
- FAST tests pass; local metrics export JSON/MD exist under `artifacts/_local/wrds_local/<run_id>` (gitignored) and the run log records their path.

## Plan
1. Stage the run log folder + existing ticket file (`docs/agent_runs/20260126_040139_ticket-10b_generate-realdata-metrics/*`, `docs/tickets/ticket-10b_generate-realdata-metrics-and-resume-snippet.md`).
2. Update WRDS local runbook guidance in `docs/RUNBOOK.md` (AX162-S vs worker_default) and keep the `pyarrow` note.
3. Append ticket-10b finish notes to `PROGRESS.md` and `docs/DECISIONS.md`.
4. Run the provided FAST + local WRDS command and record it in `docs/agent_runs/20260126_040139_ticket-10b_generate-realdata-metrics/COMMANDS.md` + `TESTS.md`.
5. Revert `docs/artifacts/manifest.json` and confirm no diffs under `docs/artifacts/wrds/`.
6. Generate the GPT review bundle with `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-10b_finish_track_runlog_and_clean_manifest`.

## Notes
- Keep local WRDS exports under `artifacts/_local/wrds_local/` (gitignored) and avoid logging restricted identifiers.
- Use a dateset clone with `wrds_local_root: /srv/data/wrds/wrds` if the whitelist only allows `WRDS_LOCAL_ROOT=/srv/data/wrds`.

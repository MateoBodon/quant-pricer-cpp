# Prompt

Ticket: **16**
Run: **20260216_024908_ticket-16**
Summary: WRDS local parquet metrics resume refresh

## Goal
Close the FAIL verdict by making ticket-16 auditable and reproducible:
- track the ticket-16 run log in git,
- replace non-reproducible `python3 - <<'PY' ...` placeholders with full commands,
- add the missing ticket file,
- surface headline aggregate real-data metrics for resume updates,
- implement a sample-testable snippet generator for `metrics_export_{sample,local}.json`.

## Constraints
- Keep local-only outputs under `artifacts/_local/`.
- Do not commit raw WRDS data or row-level records.
- Snippet output must remain aggregate-only and sanitized (no `/srv/data/wrds`, `.parquet`, `.csv`).
- Provide run evidence under `docs/agent_runs/20260216_024908_ticket-16/`.

## Planned deliverables
- `scripts/generate_wrds_resume_snippet.py`
- `tests/test_wrds_resume_snippet_from_sample_export_fast.py`
- `docs/RUNBOOK.md` update for resume snippet workflow
- `docs/tickets/ticket-16_wrds-local-parquet-metrics-resume-refresh.md`
- Updated run log files (`COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`)
- `PROGRESS.md` append/update

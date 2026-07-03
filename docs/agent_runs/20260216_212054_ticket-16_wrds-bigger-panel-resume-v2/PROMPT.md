# Prompt

Ticket: **ticket-16**
Run: **20260216_212054_ticket-16_wrds-bigger-panel-resume-v2**
Summary: WRDS larger precommitted panel refresh and resume snippet update

## Goal
- [x] Generate a larger pre-committed WRDS real-data panel export and produce an updated aggregate-only resume snippet from local outputs.

## Constraints
- [x] No new top-level directories.
- [x] Local bulky outputs stay under `artifacts/_local/`.
- [x] Do not commit raw WRDS row-level records.
- [x] Run log contains `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`.
- [x] Panel selection rule is fixed in dateset YAML before evaluating metrics.

## Plan
1. Create `wrds_pipeline_dates_panel_resume_v2.yaml` with deterministic, documented selection rule and >5 entries.
2. Run CI-safe sample smoke + sample snippet generation.
3. Run licensed local parquet export with fixed run id `wrds_local_resume_v2` and generate local resume snippet.
4. Record aggregate metrics + derived Heston-vs-BS improvement in run log and append `PROGRESS.md`.
5. Verify tracking safety and snippet sanitization expectations.

## Files touched (actual)
- `wrds_pipeline_dates_panel_resume_v2.yaml`
- `docs/agent_runs/20260216_212054_ticket-16_wrds-bigger-panel-resume-v2/PROMPT.md`
- `docs/agent_runs/20260216_212054_ticket-16_wrds-bigger-panel-resume-v2/COMMANDS.md`
- `docs/agent_runs/20260216_212054_ticket-16_wrds-bigger-panel-resume-v2/RESULTS.md`
- `docs/agent_runs/20260216_212054_ticket-16_wrds-bigger-panel-resume-v2/TESTS.md`
- `PROGRESS.md`

## Definition of Done
- [x] Dateset v2 created with deterministic rule and >5 entries.
- [x] Local run outputs generated under `artifacts/_local/wrds_local/wrds_local_resume_v2/`.
- [x] Resume snippet generated from local metrics JSON.
- [x] Headline metrics + derived improvement captured in run log.
- [x] Tracking safety check completed.

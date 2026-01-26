# ticket-10c_tracking-policy-wrds-local

## Goal
Make the WRDS local-metrics workflow TRACKING_POLICY-compliant while keeping docs/artifacts clean and tracking the missing ticket-10b docs/run log.

## Scope
- Update WRDS local output defaults to `artifacts/_local/wrds_local` (pipeline + exporter).
- Ensure local manifest/provenance writes to scratch under `artifacts/_local`.
- Update `docs/RUNBOOK.md`, `README.md`, `docs/WRDS_Results.md`, `project_state/KNOWN_ISSUES.md`, and ticket-10b docs.
- Track the ticket-10b ticket files and confirm the run log + dateset clone are tracked.
- Do not commit raw/derived WRDS outputs.

## Acceptance Criteria
- Local WRDS defaults point to `artifacts/_local` and do not require any docs/artifacts-local path.
- Local provenance writes to `artifacts/_local` (e.g., `manifest_local.json`).
- `docs/RUNBOOK.md` + ticket-10b docs reference `artifacts/_local` paths.
- Ticket-10b run log contains COMMANDS/RESULTS/TESTS/META plus dateset clone and is tracked.
- `ctest --test-dir build -L FAST --output-on-failure` passes.
- `docs/artifacts/manifest.json` remains unchanged by local runs.

## Plan
1. Update local defaults + manifest handling in `wrds_pipeline/pipeline.py`, `scripts/wrds_realdata_metrics_export.py`, and `.gitignore`.
2. Align docs in `docs/RUNBOOK.md`, `README.md`, `docs/WRDS_Results.md`, `project_state/KNOWN_ISSUES.md`, and ticket files under `docs/tickets/`.
3. Track WRDS exporter + FAST test in `scripts/wrds_realdata_metrics_export.py`, `tests/test_wrds_realdata_export_fast.py`, and `CMakeLists.txt`.
4. Run FAST tests and capture results in `docs/agent_runs/20260126_204606_ticket-10c_tracking-policy-wrds-local/TESTS.md`.
5. Generate the GPT review bundle and update repo memory docs (`PROGRESS.md`, `docs/DECISIONS.md` if needed).

## Notes
- Local artifacts stay under `artifacts/_local` and remain untracked.

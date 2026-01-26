# Ticket: ticket-10a_finish-wrds-exporter-tracked

## Goal
Finalize ticket-10 by making the WRDS real-data metrics exporter + FAST guard reviewable, tracked, and safe, while de-noising the diff.

## Scope
- Track the WRDS real-data metrics exporter + FAST test in git.
- Add safety checks so the exporter only consumes whitelisted aggregated CSVs and refuses suspicious columns.
- Verify RUNBOOK commands match current WRDS pipeline CLI flags (including `--output-root`).
- Revert unrelated regenerated artifacts (unless doing a snapshot refresh).
- Record run logs and update repo memory.

## Acceptance Criteria
- `scripts/wrds_realdata_metrics_export.py` exports sanitized JSON/MD from whitelisted aggregated files only.
- Exporter includes provenance fields: `panel_id`, date ranges, git SHA, data mode, machine label.
- Exporter refuses suspicious/unexpected columns in WRDS aggregated CSVs.
- `tests/test_wrds_realdata_export_fast.py` is tracked and passes using sample artifacts without creds.
- FAST test is registered with `ctest -L FAST`.
- `artifacts/_local/wrds_local/**` remains gitignored.
- `docs/RUNBOOK.md` commands match actual pipeline CLI flags.
- Diff excludes unrelated regenerated artifacts/validation pack (unless explicitly refreshed and documented).

## Plan
1. Add exporter safety checks (column allowlist + restricted tokens) in `scripts/wrds_realdata_metrics_export.py`.
2. Update `tests/test_wrds_realdata_export_fast.py` to validate safety checks.
3. Confirm FAST registration in `CMakeLists.txt` and RUNBOOK commands.
4. Revert unrelated artifact/doc churn and keep only ticket-10a changes.
5. Run the provided FAST + sample-export test pipeline and log results.
6. Update `PROGRESS.md`, add run log, and generate the GPT review bundle.

## Notes
- No raw WRDS/OptionMetrics data should be read or committed.
- `artifacts/_local/wrds_local/` is gitignored; exports should target this path.

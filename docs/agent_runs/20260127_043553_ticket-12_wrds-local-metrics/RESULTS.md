# Results

## Summary
- Added `scripts/reproduce_wrds_local_metrics.sh` to run the WRDS pipeline + metrics export into `artifacts/_local/wrds_local/<run_id>` with a manifest guard.
- Added FAST coverage for the one-command workflow and registered it in CMake.
- Updated RUNBOOK instructions (docs-sanity-safe wording), CHANGELOG entry, and PROGRESS log.
- Synced `project_state/CURRENT_RESULTS.md` to the latest metrics snapshot metadata generated during FAST tests.

## Key outputs
- `scripts/reproduce_wrds_local_metrics.sh`
- `tests/test_wrds_local_metrics_one_command_fast.py`
- `docs/RUNBOOK.md`
- `CHANGELOG.md`
- `project_state/CURRENT_RESULTS.md`
- `docs/agent_runs/20260127_043553_ticket-12_wrds-local-metrics/`

## Notes
- FAST tests regenerate `docs/artifacts/manifest.json` and `docs/artifacts/metrics_summary.*` metadata; headline metrics are unchanged.

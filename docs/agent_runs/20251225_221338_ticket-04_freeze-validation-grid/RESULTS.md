# Results

## Summary
- Added frozen protocol configs under `configs/scenario_grids/` and `configs/tolerances/`, and wired all headline scripts to require `--scenario-grid` + `--tolerances` with config-driven parameters.
- Recorded protocol hashes in `docs/artifacts/manifest.json` and surfaced them in `docs/artifacts/metrics_summary.*`.
- Added FAST guardrails (`tests/test_protocol_config_guard_fast.py`) to fail closed without protocol provenance and to validate the canonical configs.
- Updated `scripts/reproduce_all.sh` to pass protocol configs (and preserve metrics_summary during clean to keep FAST tests green).
- Updated `project_state/CONFIG_REFERENCE.md`, `project_state/CURRENT_RESULTS.md`, and `CHANGELOG.md`.

## Artifacts updated
- `docs/artifacts/manifest.json`
- `docs/artifacts/metrics_summary.json`
- `docs/artifacts/metrics_summary.md`
- `docs/validation_pack.zip`
- Refreshed CSV/PNG artifacts under `docs/artifacts/` (tri-engine, PDE order, MC Greeks, QL parity, benchmarks, WRDS sample)

## Bundle
- `docs/gpt_bundles/20251225T225148Z_ticket-04_20251225_221338_ticket-04_freeze-validation-grid.zip`

## Notes
- The initial run log folder `docs/agent_runs/20251225_221202_ticket-04_freeze-validation-grid/` was created during a failed bootstrap and is not the primary log for this run.

## Human merge checklist
- Headline scripts fail closed without protocol configs (no silent defaults)
- Config hashes appear in docs/artifacts/manifest.json and are referenced by metrics snapshot
- FAST tests pass and include the new guardrail
- REPRO_FAST pipeline passes and writes only to docs/artifacts
- WRDS sample smoke still passes
- PROGRESS.md + CONFIG_REFERENCE.md updated
- No secrets/raw WRDS data in diffs/logs
- Bundle generated and contains non-empty run logs + DIFF.patch

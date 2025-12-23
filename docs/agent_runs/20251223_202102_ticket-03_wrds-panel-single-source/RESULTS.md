# Results

- Canonicalized the WRDS panel config to `wrds_pipeline_dates_panel.yaml` (added `panel_id`) and removed the legacy `wrds_pipeline/dateset.yaml`.
- WRDS dateset runs now log `panel_id` and write it + `dateset_inputs` (hash) into `docs/artifacts/manifest.json` under `runs.wrds_dateset`.
- Docs refreshed to remove dual-config ambiguity and describe the canonical panel + provenance (`project_state/CONFIG_REFERENCE.md`, `project_state/PIPELINE_FLOW.md`, `project_state/ARCHITECTURE.md`, `project_state/OPEN_QUESTIONS.md`, `docs/WRDS_Results.md`, `docs/Results.md`, `docs/CODEX_SPRINT_TICKETS.md`, `CHANGELOG.md`, `PROGRESS.md`).
- Regenerated canonical artifacts and validation pack via `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`.
- Note: an attempted TESTS.md write accidentally invoked `reproduce_all.sh` via shell expansion; it was interrupted and then rerun to completion to restore artifacts.
- Assumption: `project_state/_generated/repo_inventory.json` was not regenerated; historical logs still reference the removed dateset file.

Bundle: `docs/gpt_bundles/20251223T204819Z_ticket-03_20251223_202102_ticket-03_wrds-panel-single-source.zip`

Human merge checklist:
- Only one WRDS panel config remains authoritative; the other is removed or a clearly documented alias
- Pipeline prints/logs panel id and provenance contains it
- Sample WRDS smoke ran (WRDS_USE_SAMPLE=1) and reproduce_all ran (REPRO_FAST=1 WRDS_USE_SAMPLE=1)
- No raw WRDS/OptionMetrics data or credentials in diffs/logs
- PROGRESS.md + CONFIG_REFERENCE.md updated
- Bundle generated via make gpt-bundle and contains complete non-empty run logs

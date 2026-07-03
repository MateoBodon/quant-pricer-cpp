# ticket-16_wrds-local-parquet-metrics-resume-refresh

## Goal
Generate a resume-ready, aggregate-only snippet from `metrics_export_{local,sample}.json` produced by the WRDS exporter so resume updates can use the latest real-data metrics without leaking raw/local details.

## Context
- Ticket-16 local run output exists under `artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/`.
- Current run evidence proves export execution but did not surface headline metrics in tracked docs.
- Existing one-command workflow is `scripts/reproduce_wrds_local_metrics.sh` and is documented in `docs/RUNBOOK.md`.

## Scope
- Add `scripts/generate_wrds_resume_snippet.py`.
- Add FAST test `tests/test_wrds_resume_snippet_from_sample_export_fast.py` and wire it into `CMakeLists.txt`.
- Update `docs/RUNBOOK.md` with resume-snippet usage for sample and local parquet runs.
- Update run log under `docs/agent_runs/<RUN_NAME>/` with reproducible commands, outcomes, and headline aggregate metrics.

## Constraints
- Keep local/derived outputs under `artifacts/_local/` (no tracked bulk outputs).
- Snippet must be aggregate-only and must not contain `/srv/data/wrds`, `.parquet`, `.csv`, or row-level dumps.
- Sample-mode flow must remain CI-testable via `WRDS_USE_SAMPLE=1`.

## Acceptance Criteria
- `scripts/generate_wrds_resume_snippet.py` generates snippets from both `metrics_export_sample.json` and `metrics_export_local.json`.
- Default output path is sibling `resume_snippet_wrds_{sample,local}.md` under `artifacts/_local/wrds_local/<run_id>/`.
- Sanitization guard rejects banned tokens/path/filetype leaks.
- FAST test `wrds_resume_snippet_from_sample_export_fast` passes.
- `docs/RUNBOOK.md` documents resume snippet workflow.
- Ticket-16 run log is tracked and includes real commands/outcomes.

## Test Plan
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build -j`
- `ctest --test-dir build -L FAST --output-on-failure`
- `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --run-id wrds_local_ci_snippet --dateset wrds_pipeline_dates_panel.yaml`
- `python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.json`
- Local parquet smoke (licensed host):
  - `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=<label> ./scripts/reproduce_wrds_local_metrics.sh --run-id wrds_local_resume --dateset <local_dateset>.yaml`
  - `python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_resume/metrics_export_local.json`

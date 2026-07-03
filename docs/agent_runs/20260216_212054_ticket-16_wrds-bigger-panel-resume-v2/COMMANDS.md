# Commands

Commands that changed state or produced measurable outputs.

- `git status --short`
  - Baseline clean before edits.

- `python3 tools/agentic/runlog_init.py --run-name "20260216_212054_ticket-16_wrds-bigger-panel-resume-v2" --ticket "ticket-16" --summary "WRDS larger precommitted panel refresh and resume snippet update"`
  - Created run log directory and required base files.

- `cat > wrds_pipeline_dates_panel_resume_v2.yaml <<'EOF' ...`
  - Added dateset v2 with documented pre-committed selection rule and expanded panel.

- `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_snippet`
  - First attempt failed outside venv (`ModuleNotFoundError: No module named 'matplotlib'`).

- `rm -rf artifacts/_local/wrds_local/wrds_local_ci_snippet`
- `source .venv/bin/activate && WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_snippet`
- `source .venv/bin/activate && python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.json`
  - Sample smoke + sample snippet succeeded.

- `source .venv/bin/activate && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL="$(hostname)" MPLCONFIGDIR=/tmp/matplotlib ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel_resume_v2.yaml --run-id wrds_local_resume_v2`
  - Initial v2 panel (26 entries) proved too slow for practical ticket runtime; run was terminated.

- `cat > wrds_pipeline_dates_panel_resume_v2.yaml <<'EOF' ...`
  - Revised deterministic rule to a moderate panel size (14 entries): v1 stress dates + Q1/Q3 anchors for 2020-2025.

- `rm -rf artifacts/_local/wrds_local/wrds_local_resume_v2`
- `source .venv/bin/activate && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL="$(hostname)" MPLCONFIGDIR=/tmp/matplotlib PYTHONUNBUFFERED=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel_resume_v2.yaml --run-id wrds_local_resume_v2`
  - Local parquet export succeeded; wrote `metrics_export_local.json` and `metrics_export_local.md`.

- `source .venv/bin/activate && python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.json`
  - Generated `resume_snippet_wrds_local.md`.

- `python3 - <<'PY' ...`
  - Computed derived aggregate metric: Heston-vs-BS median IV RMSE improvement percentage.

- `rg -n '/srv/data/wrds|\.parquet|\.csv' artifacts/_local/wrds_local/wrds_local_resume_v2/resume_snippet_wrds_local.md`
  - No matches (sanitization check).

- `apply_patch` on `PROGRESS.md`
  - Appended a 2026-02-16 progress entry for this run id and output folder.

- `git status --porcelain`
  - Final tracking check: only dateset + run log + `PROGRESS.md` are tracked changes.

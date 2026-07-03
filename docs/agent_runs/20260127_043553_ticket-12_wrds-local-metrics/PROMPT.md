# Prompt

Ticket: **12**
Run: **20260127_043553_ticket-12_wrds-local-metrics**
Summary: One-command WRDS local metrics export

## User prompt (verbatim)
# ticket-12 — One-command WRDS local metrics export (resume-safe)

## Goal

Add a single command that runs the WRDS pipeline + metrics exporter into a gitignored output root and prints the path to a resume-safe metrics Markdown file.

## Context

* Today, the WRDS “real data” workflow is documented but multi-step in `docs/RUNBOOK.md` (see **“WRDS real-data export”** section). The steps are easy to mis-run (wrong dateset clone, wrong root) and can accidentally cause manifest churn.
* `docs/DECISIONS.md` (2026-01-26 entries) documents why local runs must **avoid mutating tracked manifests** and why local parquet access may require a **dateset clone** pointing at `/srv/data/wrds/wrds`.
* `TRACKING_POLICY.md` requires bulky/local-only outputs to go under `artifacts/_local/` and forbids new top-level dirs.
* `project_state/CURRENT_RESULTS.md` shows the committed WRDS metric is currently from **sample mode**; we want an easy, safe way to generate **current local metrics** for resume updates without touching tracked artifacts.

## Constraints

* **Tracking / logging (must follow):**

  * Do not create new top-level directories.
  * Bulky outputs must go to `artifacts/_local/` (or `reports/_runs/`), not `docs/artifacts/`.
  * Create a run log under `docs/agent_runs/<RUN_NAME>/` for the implementation run (PROMPT/COMMANDS/RESULTS/TESTS/META) per `docs/DOCS_AND_LOGGING_SYSTEM.md`.
* **Repo-specific / data policy:**

  * Must not write raw WRDS data (or any derived datasets) into tracked paths.
  * The “one-command” workflow must **not modify** `docs/artifacts/manifest.json` or other tracked artifact files by default.
  * Must continue to fail closed if the WRDS exporter schema/columns drift (per `docs/DECISIONS.md` 2026-01-26).

## Plan

1. Create `scripts/reproduce_wrds_local_metrics.sh`:

   * `set -euo pipefail`; parse `--dateset <path>` and optional `--run-id <id>`.
   * Default `RUN_ID=wrds_local_$(date -u +%Y%m%d_%H%M%S)` and `OUT_ROOT=artifacts/_local/wrds_local/$RUN_ID`.
   * Force provenance/manifest to local-only:

     * Refuse to run if `QUANT_MANIFEST_PATH` is set to a path outside `OUT_ROOT` (fail closed).
     * Otherwise set `QUANT_MANIFEST_PATH="$OUT_ROOT/manifest_local.json"`.
   * Run pipeline with an explicit output root:

     * Sample mode: if `WRDS_USE_SAMPLE=1`, run `python3 -m wrds_pipeline.pipeline --fast --dateset <dateset> --output-root "$OUT_ROOT"`.
     * Local parquet mode: require `WRDS_LOCAL_ROOT` and run `WRDS_LOCAL_ROOT=... python3 -m wrds_pipeline.pipeline --fast --dateset <dateset> --output-root "$OUT_ROOT"`.
   * Run exporter into `OUT_ROOT`:

     * Sample: `python3 scripts/wrds_realdata_metrics_export.py --wrds-root "$OUT_ROOT" --use-sample --out "$OUT_ROOT/metrics_export_sample.json" --out-md "$OUT_ROOT/metrics_export_sample.md"`.
     * Local: `python3 scripts/wrds_realdata_metrics_export.py --wrds-root "$OUT_ROOT" --out "$OUT_ROOT/metrics_export_local.json" --out-md "$OUT_ROOT/metrics_export_local.md"`.
   * At end, print a single line with the absolute/relative path to the generated `*.md` export file.
2. Update `docs/RUNBOOK.md`:

   * Add a “one-command” section for:

     * Sample (CI-friendly): `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml`
     * Local parquet: `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=<label> ./scripts/reproduce_wrds_local_metrics.sh --dateset <local_dateset>.yaml`
   * Keep the manual multi-step commands, but clearly mark them as “manual mode / debugging only.”
3. Add a FAST test `tests/test_wrds_local_metrics_one_command_fast.py` (invoked by `ctest -L FAST`) that:

   * Runs the script in sample mode with a deterministic run id (e.g., `--run-id wrds_local_ci_smoke`).
   * Asserts the expected output files exist under `artifacts/_local/wrds_local/wrds_local_ci_smoke/`.
   * Asserts no tracked artifact files changed (e.g., hash or mtime check for `docs/artifacts/manifest.json`, or a `git diff --name-only` check that fails if anything under `docs/` changes).
4. Create the required run log folder under `docs/agent_runs/<RUN_NAME>/` and update `PROGRESS.md` with the commands run + results.

## Acceptance criteria

* [ ] `scripts/reproduce_wrds_local_metrics.sh` exists, is executable, and supports:

  * [ ] `--dateset <path>` (default: `wrds_pipeline_dates_panel.yaml`)
  * [ ] `--run-id <id>` (optional; otherwise UTC timestamped default)
  * [ ] sample mode via `WRDS_USE_SAMPLE=1`
  * [ ] local parquet mode via `WRDS_LOCAL_ROOT=...`
* [ ] The script **always** writes outputs under `artifacts/_local/wrds_local/<RUN_ID>/` and prints the generated metrics `.md` path at the end.
* [ ] The script fails closed if `QUANT_MANIFEST_PATH` would point to a tracked/unsafe location (anything outside the chosen `OUT_ROOT`).
* [ ] `docs/RUNBOOK.md` documents the new one-command workflow for both sample and local runs.
* [ ] A FAST test exists and passes in sample mode, and verifies the script does not modify tracked artifacts (especially `docs/artifacts/manifest.json`).
* [ ] A run log exists under `docs/agent_runs/<RUN_NAME>/` with required files, and `PROGRESS.md` is updated.

## Test plan

* [ ] Build + unit tests:

  * `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j`
  * `ctest --test-dir build -L FAST --output-on-failure`
* [ ] Smoke the one-command script (sample mode):

  * `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_smoke`
  * Verify: `ls artifacts/_local/wrds_local/wrds_local_ci_smoke/*metrics_export*`
* [ ] Manual (only on a host with WRDS parquet access):

  * `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=<label> ./scripts/reproduce_wrds_local_metrics.sh --dateset <local_dateset>.yaml`
* [ ] Safety check:

  * `git diff --name-only` (should show only the intended tracked changes from implementing this ticket; running the script should not dirty tracked artifacts)

## Artifacts / Outputs

* Tracked (code/docs):

  * `scripts/reproduce_wrds_local_metrics.sh`
  * `docs/RUNBOOK.md` (updated instructions)
  * `tests/test_wrds_local_metrics_one_command_fast.py`
  * `docs/agent_runs/<RUN_NAME>/{PROMPT.md,COMMANDS.md,RESULTS.md,TESTS.md,META.json}`
  * `PROGRESS.md` (new entry)
* Local-only (gitignored):

  * `artifacts/_local/wrds_local/<RUN_ID>/manifest_local.json`
  * `artifacts/_local/wrds_local/<RUN_ID>/metrics_export_{sample,local}.{json,md}`
  * Any pipeline outputs under `artifacts/_local/wrds_local/<RUN_ID>/...`

## Notes / Risks

* **Risk: accidental tracked-manifest mutation.** Mitigation: force `--output-root` to `artifacts/_local/...` and fail closed if `QUANT_MANIFEST_PATH` points anywhere else.
* **Risk: local parquet deps missing (`pyarrow`/`fastparquet`).** Mitigation: keep CI/FAST path in `WRDS_USE_SAMPLE=1` mode; document local dependency in `docs/RUNBOOK.md`.
* **Risk: license / leakage concerns.** Mitigation: exporter remains allowlist-based and should continue to fail closed (do not relax schema checks in this ticket).
* **Rollback plan:** revert `scripts/reproduce_wrds_local_metrics.sh`, the FAST test, and the `docs/RUNBOOK.md` changes; delete the run log folder for this ticket if needed (but keep PROGRESS history consistent).

## Goal (run summary)
- Add a one-command WRDS local metrics export with safe local-manifest routing and FAST coverage.

## Constraints checklist
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones).
- [x] No secrets in repo or logs.
- [ ] Tests run (or explicitly marked N/A).

## Plan (run)
1. Implement `scripts/reproduce_wrds_local_metrics.sh` with safe output root + manifest guard.
2. Update RUNBOOK + CHANGELOG.
3. Add FAST test and register in CMake.
4. Update run log + PROGRESS.

## Files touched (expected)
- scripts/reproduce_wrds_local_metrics.sh
- docs/RUNBOOK.md
- tests/test_wrds_local_metrics_one_command_fast.py
- CMakeLists.txt
- CHANGELOG.md
- PROGRESS.md
- docs/agent_runs/20260127_043553_ticket-12_wrds-local-metrics/*

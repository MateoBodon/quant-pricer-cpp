# RUNBOOK

How to run, test, and debug this repo.

## Setup
- `pip install -r requirements-dev.txt`

## Build
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build -j`

## Test
- `ctest --test-dir build -L FAST --output-on-failure`

## Reproduce (fast + sample)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

## WRDS sample pipeline
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`

## WRDS local metrics (one-command)
- Sample (CI-friendly):
  - `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml`
- Local partitioned vault:
  - `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds QUANT_MACHINE_LABEL=<label> ./scripts/reproduce_wrds_local_metrics.sh --dateset <locked_dateset>.yaml`
- Optional: `--run-id <id>` to control the output folder (defaults to `wrds_local_<UTC timestamp>`).
- The script prints the metrics Markdown path under `artifacts/_local/wrds_local/<run_id>/`.

## Update resume from WRDS export
- Generate sample snippet (CI-safe):
  - `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_snippet`
  - `python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.json`
- Generate local-vault snippet:
  - `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds QUANT_MACHINE_LABEL=<label> ./scripts/reproduce_wrds_local_metrics.sh --dateset <locked_dateset>.yaml --run-id wrds_local_resume`
  - `python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_resume/metrics_export_local.json`
- Default output is `artifacts/_local/wrds_local/<run_id>/resume_snippet_wrds_{sample,local}.md`.
- The snippet is aggregate-only by construction and hard-fails sanitization if banned tokens appear (`/srv/data/wrds`, `.parquet`, `.csv`).

## WRDS real-data export (manual mode / debugging only; AX162-S / worker_default)
- Sample run (aggregates only):
  - `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml`
  - `WRDS_USE_SAMPLE=1 QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds --use-sample --out artifacts/_local/wrds_local/metrics_export_sample.json --out-md artifacts/_local/wrds_local/metrics_export_sample.md`
- Local partitioned-vault run (writes to a gitignored root):
  - The authoritative root is `/Volumes/Storage/Data/wrds`; the adapter is
    pinned to snapshot `20260707_045553_global_project_priority`.
  - `RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S)`
  - `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds python3 -m wrds_pipeline.pipeline --fast --dateset <locked_dateset>.yaml --output-root artifacts/_local/wrds_local/$RUN_ID`
  - `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds QUANT_MACHINE_LABEL=<label> python3 scripts/wrds_realdata_metrics_export.py --wrds-root artifacts/_local/wrds_local/$RUN_ID --out artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.json --out-md artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.md`
  - Every per-date directory must contain `source_receipt.json`, binding the
    exact compressed inputs and acquisition manifests. Local runs also write
    `manifest_local.json` unless `QUANT_MANIFEST_PATH` is set.
  - Missing/multiple SPX identity, spot, curve, dividend, partition, or
    manifest bindings are hard failures. Do not bypass them with constants or
    sample data. Legacy monolithic parquet is not eligible for the flagship.

## Common troubleshooting
- If CMake cache is stale, remove the build directory and reconfigure.
- If Python deps are missing, rerun the setup command.

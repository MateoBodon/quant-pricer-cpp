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

## WRDS real-data export (AX162-S / worker_default)
- Sample run (aggregates only):
  - `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml`
  - `WRDS_USE_SAMPLE=1 QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds --use-sample --out artifacts/_local/wrds_local/metrics_export_sample.json --out-md artifacts/_local/wrds_local/metrics_export_sample.md`
- Local parquet run (writes to gitignored root):
  - AX162-S (parquet root at `/srv/data/wrds/wrds`):
    - `RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S)`
    - `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml --output-root artifacts/_local/wrds_local/$RUN_ID`
    - `WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root artifacts/_local/wrds_local/$RUN_ID --out artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.json --out-md artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.md`
  - worker_default (WRDS_LOCAL_ROOT allowlist is `/srv/data/wrds`; parquet root nested at `/srv/data/wrds/wrds`):
    - Clone `wrds_pipeline_dates_panel.yaml` with `wrds_local_root: /srv/data/wrds/wrds`.
    - `RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S)`
    - `WRDS_LOCAL_ROOT=/srv/data/wrds python3 -m wrds_pipeline.pipeline --fast --dateset <local_dateset>.yaml --output-root artifacts/_local/wrds_local/$RUN_ID`
    - `WRDS_LOCAL_ROOT=/srv/data/wrds QUANT_MACHINE_LABEL=worker_default python3 scripts/wrds_realdata_metrics_export.py --wrds-root artifacts/_local/wrds_local/$RUN_ID --out artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.json --out-md artifacts/_local/wrds_local/$RUN_ID/metrics_export_local.md`
  - Local runs write provenance to `artifacts/_local/wrds_local/<run_id>/manifest_local.json` unless `QUANT_MANIFEST_PATH` is set.
  - Note: `WRDS_LOCAL_ROOT` must resolve to a directory that contains `raw/optionm` parquet directories (often `/srv/data/wrds/wrds`). If your data lives elsewhere, set `wrds_local_root` in a dateset clone.
  - Parquet reads require `pyarrow` (or `fastparquet`) installed in the venv.

## Common troubleshooting
- If CMake cache is stale, remove the build directory and reconfigure.
- If Python deps are missing, rerun the setup command.

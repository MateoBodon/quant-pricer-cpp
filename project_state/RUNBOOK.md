# Runbook

## Environment

Prefer `python3` on macOS. If using the repo venv:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Optional Python binding build:

```bash
cmake -S . -B build-py -DQUANT_ENABLE_PYBIND=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build-py -j
```

## Fast Validation

```bash
ctest --test-dir build -L FAST --output-on-failure
```

Useful supporting checks:

```bash
python3 scripts/check_data_policy.py
python3 -m compileall tools/agentic/ai_os_bundle.py
```

## Official Sample Reproduction

Run this before changing headline result artifacts:

```bash
REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
python3 scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip
```

## WRDS Sample Pipeline

```bash
WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
python3 scripts/wrds_realdata_metrics_export.py --input-root docs/artifacts/wrds --output-root artifacts/_local/wrds_local/wrds_local_ci_smoke --sample
```

## WRDS Live/Local

Live WRDS and local parquet validation are explicit-only. Do not run or claim these unless the required credentials or local data root are available and the run is logged.

Common local scratch output root:

```text
artifacts/_local/wrds_local/
```

## AI OS v2 Archive And Bundles

Archive pre-v2 docs:

```bash
python3 tools/agentic/ai_os_bundle.py archive --date 20260703
```

Generate Project State Audit Bundle:

```bash
python3 tools/agentic/ai_os_bundle.py project-state \
  --timestamp <timestamp> \
  --run-dir reports/_runs/<RUN_NAME> \
  --archive-index docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_INDEX.md
```

Generate T-000 Review Bundle:

```bash
python3 tools/agentic/ai_os_bundle.py review-t000 \
  --timestamp <timestamp> \
  --run-dir reports/_runs/<RUN_NAME> \
  --archive-index docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_INDEX.md
```

## Troubleshooting

- If CMake cache errors appear, reconfigure `build/`.
- If Python tests cannot import dependencies, use `.venv/bin/python` or install `requirements-dev.txt`.
- If artifact scripts touch `artifacts/` unexpectedly, inspect `TRACKING_POLICY.md` and run the data-policy guard.
- If a doc appears stale, prefer canonical v2 docs first and use the archive index for history.

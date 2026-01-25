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

## Common troubleshooting
- If CMake cache is stale, remove the build directory and reconfigure.
- If Python deps are missing, rerun the setup command.

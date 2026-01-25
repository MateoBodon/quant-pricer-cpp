# Runbook

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

## Debug
- Reconfigure after clearing the build directory if cache errors appear.

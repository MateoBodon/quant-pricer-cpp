# Tests

- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
  - PASS (FAST + SLOW run; MARKET skipped; RngDeterminism.CounterRngThreadInvariant skipped because OpenMP not enabled).
- `ctest --test-dir build -L FAST --output-on-failure`
  - PASS (1 skipped: RngDeterminism.CounterRngThreadInvariant — OpenMP not enabled).
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
  - PASS (used a temporary `/tmp/python` shim to route to `python3`).

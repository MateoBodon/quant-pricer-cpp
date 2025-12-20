# Tests

- `ctest --test-dir build -L FAST --output-on-failure` (initial run failed: metrics_snapshot_fast blocked by missing required artifacts after hard gate).
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (runs FAST + SLOW labels; FAST passed, SLOW passed; RngDeterminism.CounterRngThreadInvariant skipped because OpenMP not enabled).
- `ctest --test-dir build -L FAST --output-on-failure` (rerun after artifacts generated: passed; same OpenMP skip).

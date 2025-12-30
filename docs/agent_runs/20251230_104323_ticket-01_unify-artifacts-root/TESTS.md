# Tests

- `ctest --test-dir build -L FAST --output-on-failure` — FAIL (SyntaxError in `tests/test_artifacts_root_guard_fast.py`, f-string quoting).
- `ctest --test-dir build -L FAST --output-on-failure` — FAIL (metrics_snapshot_fast: CURRENT_RESULTS missing generated_at).
- `ctest --test-dir build -L FAST --output-on-failure` — PASS (RngDeterminism.CounterRngThreadInvariant skipped: OpenMP not enabled).
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` — PASS (FAST + SLOW ran; MARKET skipped; validation pack written).
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — PASS.
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` — PASS (rerun after protocol_config_guard manifest isolation; FAST + SLOW ran; MARKET skipped; validation pack written).

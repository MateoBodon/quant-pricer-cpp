# Tests

- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` — **FAILED** (FAST tests inside reproduce_all failed: `heston_calibration_fast`, `qmc_vs_prng_equal_time_fast`, `greeks_reliability_fast`, `heston_series_fast`, `parity_checks_fast`, `heston_safety_fast`; root cause: `ModuleNotFoundError: No module named 'matplotlib'`).
- `ctest --test-dir build -L FAST --output-on-failure` — **FAILED** (same six FAST tests; one skipped: `RngDeterminism.CounterRngThreadInvariant`).
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` — **FAILED** (`python` not on PATH).
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — **PASSED**.

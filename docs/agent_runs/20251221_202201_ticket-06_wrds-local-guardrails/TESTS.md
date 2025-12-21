# Tests

1) `ctest --test-dir build -L FAST --output-on-failure`
   - Result: PASSED (100% tests passed, 55 tests; skipped: RngDeterminism.CounterRngThreadInvariant)

2) `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
   - Result: FAILED (`zsh:1: command not found: python`)

3) `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
   - Result: PASSED (`[wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample`)

4) `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
   - Result: PASSED
   - FAST label: 55 tests passed; skipped: RngDeterminism.CounterRngThreadInvariant
   - SLOW label: 7 tests passed
   - MARKET label: skipped (RUN_MARKET_TESTS=0)

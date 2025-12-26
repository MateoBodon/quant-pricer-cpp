# Tests

## Manual runs
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (pass)
- `cmake --build build -j` (pass)
- `ctest --test-dir build -L FAST --output-on-failure` (failed; ql_parity CSV missing bucket columns before regeneration)
- `ctest --test-dir build -L FAST --output-on-failure` (failed; CURRENT_RESULTS missing metrics_summary generated_at)
- `ctest --test-dir build -L FAST --output-on-failure` (pass; after updating CURRENT_RESULTS)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (failed; metrics_snapshot_fast mismatch on CURRENT_RESULTS)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (pass; FAST + SLOW ran, MARKET skipped)
- `ctest --test-dir build -L FAST --output-on-failure` (pass; final verification after CURRENT_RESULTS update)

## Notes
- One FAST test (`RngDeterminism.CounterRngThreadInvariant`) was skipped due to OpenMP not enabled (expected).

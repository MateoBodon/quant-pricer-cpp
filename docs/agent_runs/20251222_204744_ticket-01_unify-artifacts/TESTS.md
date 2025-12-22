# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (pass; OpenMP not found warning)
- `cmake --build build -j` (pass)
- `ctest --test-dir build -L FAST --output-on-failure` (pass; `RngDeterminism.CounterRngThreadInvariant` skipped due to OpenMP)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (pass; FAST+SLOW ran, MARKET skipped; Heston MC diagnostic warnings emitted)
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` (failed: `python` not on PATH)
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` (pass)

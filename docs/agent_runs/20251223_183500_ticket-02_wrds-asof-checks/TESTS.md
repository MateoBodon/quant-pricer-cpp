# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` — PASS
- `cmake --build build -j` — PASS
- `ctest --test-dir build -L FAST --output-on-failure` — PASS (58 tests; 1 skipped: RngDeterminism.CounterRngThreadInvariant)
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — PASS
  - Output: `[wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample`

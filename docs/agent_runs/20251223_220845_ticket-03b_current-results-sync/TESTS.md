# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (pass; OpenMP not found in configure output).
- `cmake --build build -j` (pass).
- `ctest --test-dir build -L FAST --output-on-failure` (failed initially: `metrics_snapshot_fast` AssertionError: CURRENT_RESULTS missing QMC vs PRNG highlight metrics).
- `ctest --test-dir build -L FAST --output-on-failure` (failed again before regex fix; same AssertionError).
- `python3 tests/test_metrics_snapshot_fast.py` (failed before regex fix; same AssertionError).
- `python3 tests/test_metrics_snapshot_fast.py` (pass; wrote metrics_summary.json/metrics_summary.md).
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` (pass; output: `[wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample`).
- `ctest --test-dir build -L FAST --output-on-failure` (pass; 58 tests, 0 failed; `RngDeterminism.CounterRngThreadInvariant` skipped).

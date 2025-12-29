# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` — pass.
- `cmake --build build -j` — pass.
- `ctest --test-dir build -L FAST --output-on-failure` — pass (58 tests, 1 skipped: `RngDeterminism.CounterRngThreadInvariant` due to OpenMP not enabled).
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` — fail:
  ```
  zsh:1: command not found: python
  ```
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — pass.
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` — pass (FAST + SLOW ran; MARKET skipped).
- `if [ -d artifacts ]; then (find artifacts -type f | head -n 50; exit 1); fi` — pass.

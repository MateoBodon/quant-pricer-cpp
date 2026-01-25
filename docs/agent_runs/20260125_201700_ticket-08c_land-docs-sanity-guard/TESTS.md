# TESTS

- Failed: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`
  - Error: CMakeCache from `/Users/mateobodon/...` vs `/home/codex/...`.
- Failed: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`
  - Errors: missing `matplotlib`/`numpy` for FAST python scripts.
- Failed: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/tmp/quant-pricer-venv/bin/python3 && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`
  - Error: `metrics_snapshot_fast` still used system `python3` (missing numpy).
- Passed: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/tmp/quant-pricer-venv/bin/python3 && cmake --build build -j && PATH=/tmp/quant-pricer-venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure && PATH=/tmp/quant-pricer-venv/bin:$PATH ctest --test-dir build -R docs_sanity_fast --output-on-failure`.

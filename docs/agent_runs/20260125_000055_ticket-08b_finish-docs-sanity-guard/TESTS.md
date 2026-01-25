# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` — PASS.
- `cmake --build build -j` — PASS.
- `ctest --test-dir build -L FAST --output-on-failure` — PASS (RngDeterminism.CounterRngThreadInvariant skipped: OpenMP not enabled).
- `ctest --test-dir build -R docs_sanity_fast --output-on-failure` — PASS.

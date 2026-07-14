# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` — PASS.
- `cmake --build build -j` — PASS.
- `ctest --test-dir build -L FAST --output-on-failure` — 60 passed, 1 skipped, 2 failed on the first run. `metrics_snapshot_fast` failed because the suite regenerated tracked snapshot files; those test-side-effect changes were restored. `gpt_bundle_empty_diff_fast` failed on missing baseline-required documentation files before reaching its expected empty-range assertion.
- `ctest --test-dir build -R '^(docs_sanity_fast|data_policy_guard_fast|cli_smoke_fast)$' --output-on-failure` — PASS: 3/3.
- Published C++ snippet syntax check plus installed-package consumer configure/build/run — PASS; probe returned `8.82732`.

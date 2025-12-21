---
generated_at: 2025-12-20T21:11:15Z
git_sha: 36c52c1d72dbcaacd674729ea9ab4719b3fd6408
branch: master
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - rg --files
  - rg --files -g '*.py'
  - python3 tools/project_state_generate.py
  - uname -a
  - cmake --version
---

# Test Coverage

## Test suites
- C++ unit tests: `tests/*.cpp` built into `unit_tests` via CMake (`CMakeLists.txt`).
- Python FAST tests: `tests/test_*_fast.py` (invoked via `ctest -L FAST`).
- WRDS MARKET tests: `wrds_pipeline/tests/test_wrds_pipeline.py` (label `MARKET`, skips without WRDS env).
- Benchmarks: `benchmarks/*.cpp` executed via `ctest -L BENCH` or `make bench`.

## Test entrypoints
- Fast loop: `ctest --test-dir build -L FAST --output-on-failure`.
- Full suite: `ctest --test-dir build --output-on-failure`.
- MARKET tests: `ctest --test-dir build -L MARKET --output-on-failure` (requires WRDS credentials).

## Coverage artifacts
- Coverage HTML appears under `docs/coverage/` (generated in CI / release workflows).
- Current coverage percentages are not extracted in this rebuild; refer to the published HTML for metrics.

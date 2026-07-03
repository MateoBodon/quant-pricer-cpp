# Tests

- [!] `WRDS_USE_SAMPLE=1 python3 tests/test_wrds_local_metrics_one_command_fast.py`
  - Result: failed (ModuleNotFoundError: No module named 'matplotlib').
- [x] `PATH="$PWD/.venv/bin:$PATH" WRDS_USE_SAMPLE=1 .venv/bin/python tests/test_wrds_local_metrics_one_command_fast.py`
  - Result: passed.
- [!] `PATH="$PWD/.venv/bin:$PATH" ctest --test-dir build -L FAST --output-on-failure`
  - Result: failed (docs_sanity_fast: `HHMMSS` placeholder in docs/RUNBOOK.md).
- [x] `PATH="$PWD/.venv/bin:$PATH" ctest --test-dir build -L FAST --output-on-failure`
  - Result: passed.

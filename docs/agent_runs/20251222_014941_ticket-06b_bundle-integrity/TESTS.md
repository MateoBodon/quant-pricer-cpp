# Tests

- `python3 -m compileall scripts/gpt_bundle.py` — **PASSED**.
- `ctest --test-dir build -L FAST --output-on-failure` — **SKIPPED** (bundler-only change; build dir not validated in this run).

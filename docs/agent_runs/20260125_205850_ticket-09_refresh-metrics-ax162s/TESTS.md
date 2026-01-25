# Tests

- `PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure` (pass)
- `PATH=$PWD/.venv/bin:$PATH REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (pass; includes FAST+SLOW, MARKET skipped)
- `PATH=$PWD/.venv/bin:$PATH REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (failed first attempt: `metrics_snapshot_fast` mismatch before `CURRENT_RESULTS.md` update)

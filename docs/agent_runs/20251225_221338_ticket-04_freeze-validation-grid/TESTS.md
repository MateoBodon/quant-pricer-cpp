# Tests

## Build
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (ok; OpenMP not found)
- `cmake --build build -j` (ok)

## FAST suite
- `ctest --test-dir build -L FAST --output-on-failure` (pass; `RngDeterminism.CounterRngThreadInvariant` skipped because OpenMP is disabled)

## Official pipeline
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
  - First run: failed at `metrics_snapshot_fast` (metrics_summary.* missing after clean).
  - Second run: pass (FAST + SLOW tests ran; OpenMP-dependent test skipped).

## WRDS sample smoke
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` (ok)

## Notes
- `scripts/reproduce_all.sh` emitted the usual Heston MC deviation warnings during `heston_qe_vs_analytic.py`.

## Data policy
- `python3 scripts/check_data_policy.py` (ok)
- Negative test: added temp `docs/artifacts/forbidden_sample.csv` with `strike,market_iv` pattern, ran `python3 scripts/check_data_policy.py` (expected fail), then removed file.

## FAST re-run
- `ctest --test-dir build -L FAST --output-on-failure` (pass; `RngDeterminism.CounterRngThreadInvariant` skipped because OpenMP is disabled)

# Test Coverage

## How to Run
- C++/Python FAST label: `ctest --test-dir build -L FAST --output-on-failure`.
- Full suite (includes SLOW/benchmarks if enabled): `ctest --test-dir build --output-on-failure`.
- MARKET (WRDS opt-in): `ctest --test-dir build -L MARKET --output-on-failure` (skips with exit 77 unless WRDS env set).
- Benchmarks (lightweight): `ctest --test-dir build -L BENCH --output-on-failure`.

## Test Files & Focus
- **C++ GTest (unit_tests target)**
  - `tests/test_sanity.cpp` – basic construction/runs.
  - `tests/test_black_scholes.cpp` – BS prices/Greeks, parity checks.
  - `tests/test_mc.cpp` – MC price vs analytic with variance reduction, RNG determinism.
  - `tests/test_pde.cpp` – CN pricing, boundary modes, theta extraction.
  - `tests/test_barrier.cpp`, `tests/test_barrier_mc_regression.cpp` – RR analytics and MC regression harness.
  - `tests/test_american.cpp` – PSOR/LSMC/binomial consistency.
  - `tests/test_grid_utils.cpp` – grid assembly/stretch mapping.
  - `tests/test_digital.cpp`, `tests/test_asian.cpp`, `tests/test_lookback.cpp`, `tests/test_multi.cpp`, `tests/test_risk.cpp`.
  - `tests/test_term_structures.cpp` – piecewise schedule lookup.
  - `tests/test_heston.cpp` – analytic Heston properties; MC parity; characteristic function sanity.
  - `tests/test_rng_repro.cpp` – counter RNG determinism.
  - `tests/test_sanity.cpp` – version/basic compile TU guard.
- **Python FAST**
  - `tests/test_parity_fast.py` – multi-product parity against QuantLib/analytic.
  - `tests/test_qmc_fast.py` – QMC vs PRNG equal-time smoke.
  - `tests/test_greeks_reliability_fast.py` – MC Greek CI sanity.
  - `tests/test_heston_fast.py`, `tests/test_heston_series_fast.py`, `tests/test_heston_safety_fast.py` – Heston calibration/solver safety.
  - `tests/test_cli_fast.py` – quant_cli subcommands JSON parsing.
- **MARKET**
  - `wrds_pipeline/tests/test_wrds_pipeline.py` – runs two-date panel (stress + calm) when WRDS env present; asserts artifact existence and metric ranges.

## Coverage Status
- HTML report at `docs/coverage/index.html` (line/function coverage high; branch coverage notably lower in barrier, risk, CLI).
- Benchmarks are labelled `BENCH` and counted in CTest but not coverage.
- WRDS pipeline test is skipped in CI without credentials; pipeline logic otherwise exercised via scripts and artifacts.

## Gaps / Suggestions
- Add targeted branch tests for barrier degenerate cases (spot≈barrier, zero vol/time), risk Kupiec/Christoffersen edge cases, and CLI flag error paths.
- Extend Python tests to cover WRDS aggregation on sample data without network to improve coverage of calibrate_bs/heston and compare_bs_heston.
- Add unit coverage for PiecewiseConstant schedules in MC/PDE through small deterministic scenarios.

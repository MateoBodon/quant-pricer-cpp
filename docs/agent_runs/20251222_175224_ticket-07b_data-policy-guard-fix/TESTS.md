# Tests

- `python3 -m compileall scripts/check_data_policy.py tests/test_data_policy_fast.py`
  - Output:
    ```
    Compiling 'scripts/check_data_policy.py'...
    Compiling 'tests/test_data_policy_fast.py'...
    ```
- `python3 scripts/check_data_policy.py`
  - Output:
    ```
    [data-policy] OK: no restricted patterns found in tracked data artifacts.
    ```
- `ctest --test-dir build -L FAST --output-on-failure` — **FAILED** (initial run)
  - Output (tail):
    ```
    89% tests passed, 6 tests failed out of 56
    The following tests FAILED:
      58 - heston_calibration_fast (Failed)
      59 - qmc_vs_prng_equal_time_fast (Failed)
      60 - greeks_reliability_fast (Failed)
      61 - heston_series_fast (Failed)
      62 - parity_checks_fast (Failed)
      63 - heston_safety_fast (Failed)
    Errors while running CTest
    ```
  - Root cause: `ModuleNotFoundError: No module named 'matplotlib'` from the Python3.13 interpreter used by CMake.
- `ctest --test-dir build -L FAST --output-on-failure` — **PASSED** (after reconfiguring CMake to use Python 3.12 w/ matplotlib)
  - Output (tail):
    ```
    100% tests passed, 0 tests failed out of 56
    The following tests did not run:
    	 53 - RngDeterminism.CounterRngThreadInvariant (Skipped)
    ```
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
  - Output:
    ```
    [wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample
    ```

## Checklist verification (2025-12-22)

- `python3 scripts/check_data_policy.py`
  - Output:
    ```
    [data-policy] OK: no restricted patterns found in tracked data artifacts.
    ```
- Negative test (tracked forbidden CSV):
  - Commands:
    - `cat > data/policy_guard_negative_test.csv` (with `strike,market_iv`)
    - `git add data/policy_guard_negative_test.csv`
    - `python3 scripts/check_data_policy.py` (expected fail)
    - `git restore --staged data/policy_guard_negative_test.csv`
    - `rm -f data/policy_guard_negative_test.csv`
  - Output:
    ```
    [data-policy] FAIL: restricted patterns found in tracked data artifacts:
    data/policy_guard_negative_test.csv:1:strike,market_iv
    ```
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`
- `ctest --test-dir build -L FAST --output-on-failure` — **PASSED**
  - Output (tail):
    ```
    100% tests passed, 0 tests failed out of 56
    The following tests did not run:
    	 53 - RngDeterminism.CounterRngThreadInvariant (Skipped)
    ```

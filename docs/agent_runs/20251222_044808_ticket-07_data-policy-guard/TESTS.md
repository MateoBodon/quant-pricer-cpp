# Tests

- `python3 -m compileall scripts/check_data_policy.py`
  - Output:
    ```
    Compiling 'scripts/check_data_policy.py'...
    ```
- `python3 scripts/check_data_policy.py`
  - Output:
    ```
    [data-policy] OK: no restricted patterns found in tracked data artifacts.
    ```
- `ctest --test-dir build -L FAST --output-on-failure` — **FAILED**
  - Output (tail):
    ```
    89% tests passed, 6 tests failed out of 55
    The following tests FAILED:
      58 - heston_calibration_fast (Failed)
      59 - qmc_vs_prng_equal_time_fast (Failed)
      60 - greeks_reliability_fast (Failed)
      61 - heston_series_fast (Failed)
      62 - parity_checks_fast (Failed)
      63 - heston_safety_fast (Failed)
    Errors while running CTest
    ```
  - Root cause: `ModuleNotFoundError: No module named 'matplotlib'` (same as prior runs).
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` — **FAILED**
  - Output:
    ```
    zsh:1: command not found: python
    ```
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
  - Output:
    ```
    [wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample
    ```

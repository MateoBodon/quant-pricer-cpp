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

## Checklist validations (post-run)
- `python3 scripts/check_data_policy.py`
  - Output:
    ```
    [data-policy] OK: no restricted patterns found in tracked data artifacts.
    ```
- `git ls-files | xargs rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S`
  - Output: matches only in code/docs + command files; no data-artifact hits (also reports `ROADMAP (1).md` path split due to spaces).
- `git ls-files -z -- artifacts docs/artifacts data wrds_pipeline/sample_data | xargs -0 rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S`
  - Output: no matches (exit code 1 from `rg` when no matches).
- `rg -n "WRDS_PASSWORD|WRDS_USERNAME|password|token|secret" -S .`
  - Output: hits limited to documentation/env references and code tokens; no secrets committed.
- `python3 scripts/gpt_bundle.py --ticket ticket-07 --run-name 20251222_044808_ticket-07_data-policy-guard --verify docs/gpt_bundles/20251222T170132Z_ticket-07_20251222_044808_ticket-07_data-policy-guard.zip`
  - Output:
    ```
    [gpt-bundle] bundle verification passed: docs/gpt_bundles/20251222T170132Z_ticket-07_20251222_044808_ticket-07_data-policy-guard.zip
    ```

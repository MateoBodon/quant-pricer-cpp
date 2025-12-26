# Tests

- `python3 -m compileall scripts/gpt_bundle.py`
  - Output: `Compiling 'scripts/gpt_bundle.py'...`
- Negative empty-range bundle check:
  - Command: `BASE_SHA=8d59bea91a2430dee879202ffce5e1529963c59f python3 scripts/gpt_bundle.py --ticket ticket-04b --run-name _gpt_bundle_empty_diff_20251226_070038 --timestamp TESTEMPTY070038Z`
  - Output:
    - `[gpt-bundle] using base SHA 8d59bea91a2430dee879202ffce5e1529963c59f (explicit)`
    - `[gpt-bundle] No commits in diff range. Provide BASE_SHA=<sha> or run bundling from the feature branch. Pass --allow-empty-diff to override.`
- `python3 tests/test_gpt_bundle_empty_diff_fast.py`
  - Output: (none)
- `BASE_SHA=ed1afa725f908765c1b28b07fbc716127f7d0dab make gpt-bundle TICKET=ticket-04 RUN_NAME=20251225_221338_ticket-04_freeze-validation-grid`
  - Output:
    - `[gpt-bundle] using base SHA ed1afa725f908765c1b28b07fbc716127f7d0dab (explicit)`
    - `[gpt-bundle] wrote /Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp/docs/gpt_bundles/20251226T070044Z_ticket-04_20251225_221338_ticket-04_freeze-validation-grid.zip`

# Validation

- Project OS predeclaration: goal `goal_761f3b87e713`, decision event
  `evt_20260711T191314269270Z_325ded4e`.
- Python compilation: pass for the two benchmark scripts and dedicated FAST
  test.
- Reducer guard: pass for frequency-weighted mean/sample sigma and exclusion of
  nonpositive quote frequencies.
- Synthetic SSVI gates: exact-surface recovery, deliberate arbitrage rejection,
  dense numerical audit, and independent QuantLib comparison pass.
- Fixed real panel: exactly five predeclared date pairs and 1,239 calibration
  rows; all five SSVI analytic, numerical, finite-row, and independent-reference
  gates pass.
- Negative-result retention: the 2020-03-16/17 OOS BS win is present in the
  aggregate receipt and tracked narrative.
- Hedge numerical gate: 1,212/1,212 matched rows and 24,342/24,342 quote weight
  valid for calibrated-Heston deltas; no SSVI hedge claim is made.
- Data boundary: no new restricted data was opened or acquired, no AWS was used,
  and only code plus aggregate narrative evidence is tracked.

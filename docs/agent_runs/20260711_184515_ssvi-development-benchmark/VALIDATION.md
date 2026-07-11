# Validation

- Python compilation: pass for SSVI model, independent reference, benchmark,
  and dedicated FAST test.
- Synthetic exact-surface recovery: pass with IV RMSE below `1e-8` and price
  RMSE below `1e-5` ticks.
- Deliberately arbitrage-violating SSVI parameters: rejected by the sufficient
  condition gate.
- Independent QuantLib grid: pass, 1,089 prices per fitted real surface and no
  monotonicity, convexity, bounds, or repository-price disagreement failures.
- Fixed real development benchmark: completed both predeclared date pairs; all
  SSVI analytic, dense numerical, finite-row, and independent-reference gates
  passed.
- Data boundary: no new restricted file was opened or acquired; only aggregate
  metrics are tracked, while detailed inputs and the JSON receipt remain ignored.

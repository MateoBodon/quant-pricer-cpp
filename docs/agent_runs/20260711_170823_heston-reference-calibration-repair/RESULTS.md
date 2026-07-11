# Results

## Predeclared repair

Before optimizing observed results, the repair was fixed to:

- eliminate hard-clipped transformed optimizer coordinates and solve directly
  in physical bounded coordinates;
- broaden solver guards to cover stress regimes rather than encode the prior
  narrow SPX-like assumptions;
- use three deterministic starting points and retain all start diagnostics;
- make quadrature controls real, using scaled 96-point Gauss-Laguerre for
  calibration and 128-point output for prices and deltas;
- return raw Heston prices and fail closed on invalid implied prices rather than
  clipping output into no-arbitrage bounds;
- validate prices and bump-halved deltas independently with QuantLib's
  `AnalyticHestonEngine` at integration order 192.

The old implementation advertised a configurable quadrature point count but
always used a fixed 32-point table. It then clipped the resulting price. Its
unbounded internal optimization was mapped into physical parameters with hard
clips, creating flat, zero-gradient plateaus at the bounds. On 2020-03-16 this
produced a four-evaluation false optimum with all five parameters saturated.

## Independent reference evidence

On a fixed 27-case calm/stress grid spanning three parameter regimes, three
maturities, and three moneyness levels:

- maximum absolute price disagreement versus QuantLib: `1.75594e-06`;
- maximum absolute delta disagreement versus QuantLib: `9.50271e-09`;
- maximum QuantLib bump-halving disagreement: `7.64824e-08`;
- invalid repository deltas: `0`.

On all 1,239 aggregate surface rows in the existing five-date real replay:

- repository invalid deltas: `0` (previously `37` under the 32-point rule);
- QuantLib invalid deltas: `0`;
- price disagreement median / p95 / max:
  `$0.000164692` / `$0.00159624` / `$0.00457537`;
- price disagreement normalized by spot, median / p95 / max:
  `0.000440703` / `0.00565537` / `0.0166340` bps;
- delta disagreement median / p95 / max:
  `3.92697e-07` / `1.03856e-05` / `0.000447158`.

Aggregate-only reference receipt SHA-256:
`0654a1a7b79352ac9403a649e6176a2735027afe3526560f50897f48ffbe8e90`.

## Real calibration repair evidence

| Date | Metric | Prior | Repaired | Change |
| --- | ---: | ---: | ---: | ---: |
| 2020-03-16 | vega-weighted IV RMSE | 0.194143 | 0.0213589 | -88.998% |
| 2020-03-16 | vega-weighted IV MAE | 0.158065 | 0.0159948 | -89.881% |
| 2020-03-16 | IV p90 error (bps) | 3228.94 | 298.885 | -90.744% |
| 2020-03-16 | price RMSE (ticks) | 1375.22 | 220.785 | -83.945% |
| 2024-06-14 | vega-weighted IV RMSE | 0.0721060 | 0.0603914 | -16.246% |
| 2024-06-14 | vega-weighted IV MAE | 0.0207862 | 0.0270013 | +29.900% |
| 2024-06-14 | IV p90 error (bps) | 246.707 | 478.663 | +94.021% |
| 2024-06-14 | price RMSE (ticks) | 257.802 | 431.405 | +67.339% |

For 2020-03-16, all three starts converged to costs within `0.001%` of one
another. The selected solution is interior, with minimum normalized distance
to a bound `0.03553`, and is calibration-promotion eligible.

For 2024-06-14, all three starts again reached nearly identical costs, but
volatility-of-volatility remained at the broadened upper guard. The IV RMSE
improved while price and tail-IV errors worsened. That fit remains correctly
`boundary_saturated` and diagnostic-only. This is evidence of residual model or
surface misspecification, not a reason to move the guard again after observing
the result.

Aggregate-only calibration receipt SHA-256:
`950fdf7a2392316e9be09831201e4cd46d01cbcc8222785a011a5f4a3cdc5c16`.

## Decision

The repair is accepted as a numerical and optimizer correction. It removes the
known invalid-delta failure and materially repairs the 2020 stress calibration.
It does not establish Heston superiority over Black-Scholes or make the frozen
five-date panel promotion eligible; the 2024 boundary result remains an open
model-research target.

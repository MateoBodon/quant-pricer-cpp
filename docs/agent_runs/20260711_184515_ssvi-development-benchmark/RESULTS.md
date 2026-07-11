# Results

## Predeclared model and protocol

The benchmark uses power-law SSVI:

```text
w(k, theta) = theta/2 * [1 + rho*phi(theta)*k
                         + sqrt((phi(theta)*k + rho)^2 + 1 - rho^2)]
phi(theta) = eta * theta^(-gamma)
```

The ATM total-variance curve is strictly increasing and piecewise linear on
fixed 30d, 60d, 90d, 6m, and 1y knots. Smooth transforms enforce positive ATM
increments, `|rho| < 1`, `0 < gamma < 1`, and the sufficient SSVI wing and
butterfly conditions over the fixed 20d-400d validation domain. Calibration
uses three deterministic starts and the existing vega-times-quote weighted IV
residual. No price, IV, or metric output is clipped.

The exact development pairs were fixed before result inspection:

- 2020-03-16 to 2020-03-17;
- 2024-06-14 to 2024-06-17.

## Aggregate comparison

Across the 12 predeclared date-metric comparisons, SSVI wins 8, repaired Heston
wins 2, and tenor-flat Black-Scholes wins 2.

Two-date median metrics:

| Metric | SSVI | Repaired Heston | Tenor-flat BS |
| --- | ---: | ---: | ---: |
| In-sample IV RMSE | 0.0389320 | 0.0408751 | 0.0874110 |
| In-sample IV MAE | 0.0175194 | 0.0214980 | 0.0556481 |
| In-sample IV p90 error (bps) | 403.695 | 388.774 | 1073.64 |
| In-sample price RMSE (ticks) | 232.802 | 326.095 | 628.967 |
| Next-day IV MAE (bps) | 608.010 | 607.614 | 646.587 |
| Next-day price MAE (ticks) | 588.651 | 637.980 | 680.174 |

Relative to repaired Heston, SSVI's median IV RMSE is 4.75% lower, IV MAE is
18.51% lower, price RMSE is 28.61% lower, and next-day price MAE is 7.73%
lower. Its median IV p90 error is 3.84% worse and next-day IV MAE is 0.065%
worse, effectively a tie on that two-date reducer. Relative to tenor-flat BS,
SSVI lowers median IV RMSE by 55.46%, price RMSE by 62.99%, and next-day price
MAE by 13.46%.

## Date-level evidence

On 2020-03-16, SSVI wins all four in-sample metrics versus both comparators. It
reduces IV RMSE 41.52% and price RMSE 45.35% versus repaired Heston. The next-day
regime move is a negative result: tenor-flat BS wins both OOS reducers; SSVI IV
MAE is 1.43% worse than Heston and 18.30% worse than BS.

On 2024-06-14, Heston retains the best IV RMSE and p90 error, while SSVI has the
best IV MAE and price RMSE. On 2024-06-17 OOS, SSVI is strongest:

| OOS metric | SSVI | Repaired Heston | Tenor-flat BS |
| --- | ---: | ---: | ---: |
| IV MAE (bps) | 162.950 | 177.033 | 403.032 |
| Price MAE (ticks) | 244.533 | 339.990 | 527.997 |

This is a 7.96% IV-MAE and 28.08% price-MAE improvement over repaired Heston,
and a 59.57% / 53.69% improvement over tenor-flat BS.

## Arbitrage and independent-reference gates

Both fits pass all analytic and dense numerical gates on 81 maturities by 401
log-forward-moneyness points:

- minimum density factors: `0.335763` and `0.250278`;
- minimum calendar increments: `8.97e-07` and `7.87e-10`;
- no call monotonicity or convexity violations beyond numerical tolerance;
- all model prices and IVs finite on 480 in-sample and 488 OOS rows.

QuantLib independently repriced 1,089 points per fitted surface. All 2,178
prices were valid; maximum repository-versus-QuantLib absolute disagreement was
`2.83408e-13`.

The 2024 fit uses 96.04% of the predeclared sufficient-curvature limit. It is
arbitrage-valid with the intended safety margin, but this active structural
frontier is evidence for a future eSSVI extension rather than permission to
relax the condition after observing results.

## Claim decision

This is credible fixed-date development evidence for an arbitrage-aware SSVI
baseline and a clear improvement over forcing a universal Heston story. It is
not a public or broad-panel SSVI-superiority claim. Promotion requires a locked,
larger temporal panel that preserves the same reducers and includes the 2020
negative OOS regime.

Aggregate-only receipt SHA-256:
`044114ea6e4bd90eb835d6b1cf8950158d2f630d22972ba6985580c05bdcd0e4`.

# Results

## Frozen protocol and scope

This run extends the published power-law SSVI benchmark to every pair in the
existing `wrds_panel_calm_stress_v1` development panel. It changes no SSVI,
Heston, or tenor-flat Black-Scholes model setting, bound, multistart, objective,
arbitrage gate, or reducer after the outcomes. The fixed panel contains:

- 2020-03-16 to 2020-03-17, stress;
- 2020-03-17 to 2020-03-18, stress;
- 2022-06-13 to 2022-06-14, calm;
- 2022-06-14 to 2022-06-15, calm;
- 2024-06-14 to 2024-06-17, calm.

The input footprint is 1,239 calibration surface rows and 1,243 next-day rows.
All outputs are aggregate diagnostics; no option row or fitted parameter is
tracked.

## Aggregate outcome

SSVI wins 26 of the 30 frozen date-by-metric comparisons. Repaired Heston and
tenor-flat Black-Scholes each win 2.

| Metric | SSVI wins | Median change vs Heston | Mean change vs Heston |
| --- | ---: | ---: | ---: |
| In-sample IV RMSE | 4/5 | -29.19% | -22.03% |
| In-sample IV MAE | 5/5 | -34.68% | -26.76% |
| In-sample IV p90 | 4/5 | -37.12% | -23.81% |
| In-sample price RMSE | 5/5 | -33.67% | -32.21% |
| Next-day IV MAE | 4/5 | -0.44% | -2.43% |
| Next-day price MAE | 5/5 | -2.49% | -7.05% |

Against tenor-flat Black-Scholes, SSVI wins every in-sample comparison and 8 of
10 next-day comparisons. Its median relative changes are -84.26% in-sample IV
RMSE, -85.20% in-sample IV MAE, -80.58% in-sample price RMSE, -53.84% next-day
IV MAE, and -52.18% next-day price MAE.

## Date and regime evidence

| Date pair | Regime | SSVI wins | OOS IV MAE: SSVI / Heston / BS (bps) | OOS price MAE: SSVI / Heston / BS (ticks) |
| --- | --- | ---: | ---: | ---: |
| 2020-03-16/17 | Stress | 4/6 | 1053.07 / 1038.19 / 890.14 | 932.77 / 935.97 / 832.35 |
| 2020-03-17/18 | Stress | 6/6 | 417.60 / 417.76 / 716.11 | 336.47 / 346.87 / 559.48 |
| 2022-06-13/14 | Calm | 6/6 | 63.51 / 66.95 / 328.43 | 92.40 / 94.76 / 437.33 |
| 2022-06-14/15 | Calm | 6/6 | 154.31 / 155.00 / 334.32 | 221.84 / 224.89 / 463.96 |
| 2024-06-14/17 | Calm | 4/6 | 162.95 / 177.03 / 403.03 | 244.53 / 339.99 / 528.00 |

On the three calm dates, mean next-day SSVI IV MAE is 126.92 bps versus 132.99
for Heston, and mean price MAE is 186.26 ticks versus 219.88. On the two stress
dates, SSVI materially improves every mean in-sample reducer and slightly
improves mean next-day price MAE, 634.62 versus 641.42 ticks, but its mean
next-day IV MAE is worse, 735.34 versus 727.98 bps.

The first 2020 transition is retained adverse evidence. Tenor-flat BS wins both
next-day reducers, and Heston beats SSVI on next-day IV. The 2024 fit is also not
sanitized away: Heston wins IV RMSE and p90, while its calibration is itself
boundary-saturated.

## Arbitrage and independent-reference gates

All five SSVI fits pass the original analytic sufficient conditions and dense
81-by-401 maturity/moneyness numerical gates. Across the panel:

- minimum density factor is `0.250278`;
- minimum calendar increment is `7.86909e-10`;
- no in-sample or next-day SSVI output row is invalid;
- 5,445 independent QuantLib prices are valid;
- maximum repository-versus-QuantLib absolute price disagreement is
  `4.91222e-13`.

The 2024 fit reaches `3.8416` of the fixed `4.0` sufficient-curvature limit,
96.04%. It passes, but the narrow remaining margin is a structural research
target, not permission to relax a gate after observing results.

## Hedge diagnostic

The model-specific Heston delta is numerically valid on all 1,212 matched
surface rows and all 24,342 quote weight, with zero invalid derivatives. The
median date-level mean/sigma are -414.53/352.74 ticks for calibrated-Heston
delta and -348.35/327.63 ticks for market-IV Black-Scholes delta.

These are one-day diagnostic PnLs, not strategy returns. They do not establish
Heston hedge superiority, and no SSVI delta or SSVI hedge result is inferred.

## Claim decision

The exact statement “SSVI wins 26 of 30 comparisons on this frozen five-date
development panel while passing all static-arbitrage and independent-reference
gates” is supported on current HEAD. General or public SSVI superiority is not:
five dates are temporally narrow, one 2020 OOS transition is negative, and the
2024 fit is close to its structural curvature limit.

Aggregate-only receipt SHA-256:
`efa73ccce7d8c89cbb971294978070afb666b3b5048f107ff31db480513f53fa`.

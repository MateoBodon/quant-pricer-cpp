# SSVI Five-Date Development Panel

Without changing model settings or reducers, the arbitrage-aware SSVI surface
wins 26 of 30 calibration and next-day comparisons on the complete existing
five-date development panel. It wins next-day price on all five dates, passes
all analytic, dense numerical, finite-row, and independent QuantLib gates, and
materially outperforms tenor-flat Black-Scholes.

The evidence remains deliberately bounded. The 2020-03-16/17 transition is a
real negative OOS case, the 2024 fit is close to its fixed curvature limit, and
the hedge lane does not evaluate SSVI. This is strong fixed-panel evidence, not
a universal-superiority or strategy-return claim.

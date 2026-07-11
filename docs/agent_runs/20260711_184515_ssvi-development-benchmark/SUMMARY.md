# Arbitrage-Aware SSVI Development Benchmark

The repository now has a compact power-law SSVI surface with a monotone ATM
variance curve, sufficient no-butterfly conditions enforced by construction,
dense calendar/density/convexity gates, and independent QuantLib price checks.

On the two dates fixed before inspection, SSVI wins 8 of 12 calibration, price,
and next-day comparisons. It materially improves the repaired Heston's median
IV MAE and price metrics and is especially strong on the 2024 stress OOS pair.
The 2020 next-day pair remains a clear negative regime where tenor-flat BS wins.
The result is an impressive and honest development benchmark, not a universal
superiority claim.

# Heston Reference and Calibration Repair

The bounded repair replaces a hard-clipped, fixed-32-point calibration path
with physical bounded multistart optimization, genuine scaled Gauss-Laguerre
controls, raw-price fail-closed behavior, and an independent QuantLib price and
delta oracle. It eliminates all 37 previously invalid real-panel deltas and
agrees closely with QuantLib across synthetic stress cases and 1,239 real
aggregate surface rows.

The real calibration evidence is intentionally mixed. The pathological
2020-03-16 fit improves IV RMSE by 89.0% and becomes interior and eligible. The
2024-06-14 fit improves IV RMSE by 16.2% but worsens price and tail-IV metrics
and still reaches the broadened volatility-of-volatility guard, so it remains
diagnostic-only. The outcome supports the numerical repair, not a Heston
superiority claim.

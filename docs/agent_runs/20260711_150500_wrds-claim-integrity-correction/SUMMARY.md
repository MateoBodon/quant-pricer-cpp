# WRDS Claim-Integrity Correction

Independent review accepted the original run's exact 14-file provenance but
rejected its Heston risk attribution and calibration robustness. This change
repairs those defects at the source: it separates market-IV Black-Scholes and
calibrated-Heston delta hedges, makes fit saturation machine-readable, and
prevents boundary-saturated calibrations or invalid numerical derivatives from
supporting risk or superiority promotion. The first exact real replay from the
stable implementation commit exposed 37 no-arbitrage-invalid Heston deltas on
the 2024-06-14 surface. The corrected path records that evidence and nulls the
affected Heston hedge aggregates rather than clipping or aborting the remaining
provenance-clean run. The frozen five-date replay then completed from commit
`2ccbf543`: Heston improved median next-day IV MAE but lost on median in-sample
IV and price RMSE, while three fits remained boundary-saturated and 37
derivatives remained invalid. This is a strong real-data integrity result and a
clear model-repair target, not Heston-superiority evidence.

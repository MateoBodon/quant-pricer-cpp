#!/usr/bin/env python3
"""Vectorized vanilla portfolio risk and exact stress example."""

from __future__ import annotations

import numpy as np
import pyquant_pricer as qp


# option_type, quantity, spot, strike, rate, dividend, volatility, time
positions = np.array(
    [
        [1, 120, 100, 95, 0.03, 0.01, 0.22, 90 / 365],
        [-1, -80, 100, 105, 0.03, 0.01, 0.25, 90 / 365],
        [1, 50, 100, 110, 0.03, 0.01, 0.28, 180 / 365],
    ],
    dtype=np.float64,
)

risk = qp.bs_portfolio_risk(positions)
print(dict(zip(risk["total_columns"], risk["portfolio_totals"])))

# spot_return, volatility_shift, rate_shift, dividend_shift, time_elapsed
shocks = np.array(
    [
        [0.00, 0.00, 0.000, 0.000, 0 / 365],
        [-0.10, 0.08, 0.010, 0.000, 1 / 365],
        [0.08, -0.03, -0.005, 0.002, 5 / 365],
    ],
    dtype=np.float64,
)

aggregate = qp.bs_portfolio_scenarios(positions, shocks, detail=False)
print("scenario P&L:", aggregate["portfolio_pnl"])

# Request detail only when position attribution is needed. Its payload is
# scenario_count * position_count * 8 bytes.
detail = qp.bs_portfolio_scenarios(positions, shocks, detail=True)
print("position P&L attribution:\n", detail["position_pnl"])

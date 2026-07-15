#!/usr/bin/env python3
"""Installed-wheel smoke for the Python Heston analytic product surface."""

from __future__ import annotations

import math
import unittest

import pyquant_pricer as qp


class PythonHestonAnalyticBindingTest(unittest.TestCase):
    def test_black_scholes_binding_matches_independent_formula(self) -> None:
        spot, strike, rate, dividend, vol, tenor = 100.0, 105.0, 0.02, 0.0, 0.25, 0.5
        root_t = math.sqrt(tenor)
        d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * tenor) / (
            vol * root_t
        )
        d2 = d1 - vol * root_t

        def normal_cdf(x: float) -> float:
            return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

        expected = spot * math.exp(-dividend * tenor) * normal_cdf(
            d1
        ) - strike * math.exp(-rate * tenor) * normal_cdf(d2)
        self.assertAlmostEqual(
            qp.bs_call(spot, strike, rate, dividend, vol, tenor), expected, places=12
        )

    def test_heston_analytic_surface_is_usable(self) -> None:
        params = qp.HestonParams()
        params.kappa, params.theta, params.sigma, params.rho, params.v0 = (
            1.5,
            0.04,
            0.6,
            -0.45,
            0.04,
        )
        market = qp.HestonMarket()
        market.spot, market.strike = 100.0, 95.0
        market.rate, market.dividend, market.time = 0.015, 0.005, 0.75
        self.assertAlmostEqual(
            qp.heston_call_analytic(market, params), 9.576102069082546, places=12
        )
        self.assertAlmostEqual(
            qp.heston_implied_vol(market, params), 0.1895560629312405, places=12
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

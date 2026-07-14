#!/usr/bin/env python3
"""Installed-wheel evaluator for the native-backed scalar Heston put API."""

from __future__ import annotations

import math
import unittest

import numpy as np
import pyquant_pricer as qp


def objects(market_row: np.ndarray, param_row: np.ndarray) -> tuple[object, object]:
    market = qp.HestonMarket()
    market.spot, market.strike, market.rate, market.dividend, market.time = market_row
    parameter = qp.HestonParams()
    parameter.kappa, parameter.theta, parameter.sigma, parameter.rho, parameter.v0 = (
        param_row
    )
    return market, parameter


class PythonHestonAnalyticPutTest(unittest.TestCase):
    def test_scalar_put_matches_discounted_parity(self) -> None:
        params = np.array([1.5, 0.04, 0.6, -0.45, 0.04])
        markets = np.array(
            [
                [100.0, 80.0, 0.015, 0.005, 0.25],
                [100.0, 100.0, 0.0, 0.0, 1.0],
                [100.0, 120.0, -0.005, 0.01, 2.0],
                [75.0, 100.0, 0.03, 0.0, 0.5],
                [125.0, 90.0, 0.01, 0.02, 1.5],
            ]
        )
        for row in markets:
            market, parameter = objects(row, params)
            call = qp.heston_call_analytic(market, parameter)
            put = qp.heston_put_analytic(market, parameter)
            expected = (
                call
                - row[0] * math.exp(-row[3] * row[4])
                + row[1] * math.exp(-row[2] * row[4])
            )
            self.assertTrue(math.isfinite(put))
            self.assertAlmostEqual(put, expected, delta=4.0e-14)

    def test_scalar_and_batch_puts_share_native_result(self) -> None:
        markets = np.array(
            [[100.0, 90.0, 0.01, 0.005, 1.0], [100.0, 110.0, 0.01, 0.005, 1.0]]
        )
        params = np.array(
            [[1.5, 0.04, 0.6, -0.45, 0.04], [1.5, 0.04, 0.6, -0.45, 0.04]]
        )
        expected = [
            qp.heston_put_analytic(*objects(market, parameter))
            for market, parameter in zip(markets, params)
        ]
        np.testing.assert_array_equal(
            qp.heston_puts_analytic_batch(markets, params), expected
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

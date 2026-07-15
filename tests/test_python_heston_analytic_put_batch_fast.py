#!/usr/bin/env python3
"""Installed-wheel evaluator for analytic Heston put batches."""

from __future__ import annotations

import concurrent.futures
import math
import unittest

import numpy as np
import pyquant_pricer as qp


def make_inputs(count: int, offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    markets = np.empty((count, 5), dtype=np.float64)
    params = np.empty((count, 5), dtype=np.float64)
    for index in range(count):
        point = index + offset
        markets[index] = [
            80.0 + float(point % 47),
            75.0 + float((3 * point) % 59),
            -0.005 + 0.005 * float(point % 7),
            0.0025 * float(point % 5),
            0.125 + 0.125 * float(point % 16),
        ]
        params[index] = [
            1.1 + 0.1 * float(point % 5),
            0.04,
            0.35 + 0.05 * float(point % 4),
            -0.6,
            0.04,
        ]
    return markets, params


def scalar_call(market_row: np.ndarray, param_row: np.ndarray) -> float:
    market = qp.HestonMarket()
    market.spot, market.strike, market.rate, market.dividend, market.time = market_row
    parameter = qp.HestonParams()
    parameter.kappa, parameter.theta, parameter.sigma, parameter.rho, parameter.v0 = (
        param_row
    )
    return qp.heston_call_analytic(market, parameter)


class PythonHestonAnalyticPutBatchTest(unittest.TestCase):
    def test_put_batch_matches_independent_scalar_parity(self) -> None:
        markets, params = make_inputs(65)
        expected = []
        for market, parameter in zip(markets, params):
            call = scalar_call(market, parameter)
            expected.append(
                call
                - market[0] * math.exp(-market[3] * market[4])
                + market[1] * math.exp(-market[2] * market[4])
            )
        actual = qp.heston_puts_analytic_batch(markets, params)
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=4.0e-14)
        self.assertTrue(np.all(np.isfinite(actual)))

    def test_put_batch_reuses_fail_closed_validation(self) -> None:
        markets, params = make_inputs(3)
        with self.assertRaisesRegex(ValueError, "non-empty"):
            qp.heston_puts_analytic_batch(np.empty((0, 5)), np.empty((0, 5)))
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_puts_analytic_batch(markets, params[:2])
        with self.assertRaisesRegex(ValueError, "shape"):
            qp.heston_puts_analytic_batch(markets[:, :4], params)
        invalid = params.copy()
        invalid[0, 3] = 1.0
        with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
            qp.heston_puts_analytic_batch(markets, invalid)

    def test_concurrent_put_callers_are_deterministic(self) -> None:
        inputs = [make_inputs(64, offset=1000 * index) for index in range(8)]
        expected = [
            qp.heston_puts_analytic_batch(markets, params) for markets, params in inputs
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(qp.heston_puts_analytic_batch, markets, params)
                for markets, params in inputs
            ]
            actual = [future.result(timeout=10.0) for future in futures]
        for concurrent_prices, serial_prices in zip(actual, expected):
            np.testing.assert_array_equal(concurrent_prices, serial_prices)
        self.assertEqual(
            qp.heston_analytic_batch_policy(),
            {"max_process_workers": 4, "items_per_worker": 32},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

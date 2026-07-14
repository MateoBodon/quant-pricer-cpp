#!/usr/bin/env python3
"""Installed-wheel evaluator for batch analytic Heston implied volatility."""

from __future__ import annotations

import concurrent.futures
import unittest

import numpy as np
import pyquant_pricer as qp


def scalar_implied_vol(market_row: np.ndarray, parameter_row: np.ndarray) -> float:
    market = qp.HestonMarket()
    market.spot, market.strike, market.rate, market.dividend, market.time = market_row
    parameter = qp.HestonParams()
    parameter.kappa, parameter.theta, parameter.sigma, parameter.rho, parameter.v0 = parameter_row
    return qp.heston_implied_vol(market, parameter)


def make_inputs(count: int, offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    markets = np.empty((count, 5), dtype=np.float64)
    for index in range(count):
        point = index + offset
        markets[index] = [
            100.0,
            80.0 + float(point % 41),
            0.005 + 0.005 * float(point % 4),
            0.0025 * float(point % 3),
            0.25 + 0.25 * float(point % 8),
        ]
    parameter = np.array([[1.5, 0.04, 0.6, -0.45, 0.04]], dtype=np.float64)
    return markets, parameter


class PythonHestonImpliedVolBatchTest(unittest.TestCase):
    def test_broadcast_batch_is_exactly_scalar(self) -> None:
        markets, parameter = make_inputs(65)
        expected = np.array([scalar_implied_vol(row, parameter[0]) for row in markets])
        actual = qp.heston_implied_vols_batch(markets, parameter)
        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(np.all(np.isfinite(actual)))
        self.assertTrue(actual.flags.c_contiguous)

    def test_distinct_parameter_rows_are_exactly_scalar(self) -> None:
        markets, parameter = make_inputs(8)
        parameters = np.repeat(parameter, len(markets), axis=0)
        parameters[:, 0] += np.arange(len(markets), dtype=np.float64) * 0.05
        expected = np.array(
            [scalar_implied_vol(market, params) for market, params in zip(markets, parameters)]
        )
        np.testing.assert_array_equal(qp.heston_implied_vols_batch(markets, parameters), expected)

    def test_validation_matches_price_batches(self) -> None:
        markets, parameter = make_inputs(4)
        with self.assertRaisesRegex(ValueError, "non-empty"):
            qp.heston_implied_vols_batch(np.empty((0, 5)), np.empty((0, 5)))
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_implied_vols_batch(markets, np.repeat(parameter, 2, axis=0))
        invalid = markets.copy()
        invalid[0, 0] = 0.0
        with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
            qp.heston_implied_vols_batch(invalid, parameter)

    def test_concurrent_callers_are_deterministic_under_shared_policy(self) -> None:
        inputs = [make_inputs(64, offset=1000 * index) for index in range(8)]
        expected = [qp.heston_implied_vols_batch(*inputs_for_call) for inputs_for_call in inputs]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(qp.heston_implied_vols_batch, *item) for item in inputs]
            actual = [future.result(timeout=10.0) for future in futures]
        for concurrent_vols, serial_vols in zip(actual, expected):
            np.testing.assert_array_equal(concurrent_vols, serial_vols)
        self.assertEqual(
            qp.heston_analytic_batch_policy(),
            {"max_process_workers": 4, "items_per_worker": 32},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

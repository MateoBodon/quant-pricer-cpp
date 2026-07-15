#!/usr/bin/env python3
"""Installed-wheel evaluator for the Python Heston analytic batch API."""

from __future__ import annotations

import math
import unittest

import numpy as np
import pyquant_pricer as qp


def make_inputs(count: int) -> tuple[np.ndarray, np.ndarray]:
    markets = np.empty((count, 5), dtype=np.float64)
    params = np.empty((count, 5), dtype=np.float64)
    for index in range(count):
        markets[index] = [
            100.0,
            80.0 + float(index % 41),
            0.015,
            0.005,
            0.25 + 0.25 * float(index % 8),
        ]
        params[index] = [1.5, 0.04, 0.6, -0.45, 0.04]
    return markets, params


def scalar_objects(
    market_row: np.ndarray, param_row: np.ndarray
) -> tuple[object, object]:
    market = qp.HestonMarket()
    market.spot, market.strike, market.rate, market.dividend, market.time = market_row
    parameter = qp.HestonParams()
    parameter.kappa, parameter.theta, parameter.sigma, parameter.rho, parameter.v0 = (
        param_row
    )
    return market, parameter


class PythonHestonAnalyticBatchTest(unittest.TestCase):
    def test_batch_matches_scalar_elementwise(self) -> None:
        markets, params = make_inputs(32)
        scalar_inputs = [
            scalar_objects(markets[index], params[index])
            for index in range(len(markets))
        ]
        expected = [
            qp.heston_call_analytic(market, parameter)
            for market, parameter in scalar_inputs
        ]
        actual = qp.heston_calls_analytic_batch(markets, params)
        self.assertEqual(len(actual), len(expected))
        for batch_price, scalar_price in zip(actual, expected):
            self.assertTrue(math.isfinite(batch_price))
            self.assertEqual(batch_price, scalar_price)

    def test_batch_rejects_empty_or_mismatched_inputs(self) -> None:
        markets, params = make_inputs(3)
        with self.assertRaisesRegex(ValueError, "non-empty"):
            qp.heston_calls_analytic_batch(np.empty((0, 5)), np.empty((0, 5)))
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_calls_analytic_batch(markets, params[:2])
        with self.assertRaisesRegex(ValueError, "shape"):
            qp.heston_calls_analytic_batch(markets[:, :4], params)
        invalid = markets.copy()
        invalid[0, 1] = 0.0
        with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
            qp.heston_calls_analytic_batch(invalid, params)

    def test_large_batch_threaded_path_matches_scalar_samples(self) -> None:
        markets, params = make_inputs(512)
        batch = qp.heston_calls_analytic_batch(markets, params)
        self.assertEqual(batch.shape, (512,))
        self.assertTrue(np.isfinite(batch).all())

        # Counts above 32 exercise the bounded worker path. Check samples across
        # the full result rather than gating correctness on shared-runner timing.
        for index in (0, 127, 255, 511):
            market, parameter = scalar_objects(markets[index], params[index])
            self.assertEqual(batch[index], qp.heston_call_analytic(market, parameter))


if __name__ == "__main__":
    unittest.main(verbosity=2)

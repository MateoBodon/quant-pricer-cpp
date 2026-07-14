#!/usr/bin/env python3
"""Installed-wheel evaluator for the Python Heston analytic batch API."""

from __future__ import annotations

import math
import statistics
import time
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

    def test_batch_reduces_per_option_python_call_overhead(self) -> None:
        markets, params = make_inputs(128)
        scalar_inputs = [
            scalar_objects(markets[index], params[index])
            for index in range(len(markets))
        ]

        def scalar_round() -> None:
            for market, parameter in scalar_inputs:
                qp.heston_call_analytic(market, parameter)

        def batch_round() -> None:
            qp.heston_calls_analytic_batch(markets, params)

        scalar_round()
        batch_round()
        scalar_seconds: list[float] = []
        batch_seconds: list[float] = []
        for _ in range(7):
            start = time.perf_counter()
            scalar_round()
            scalar_seconds.append(time.perf_counter() - start)
            start = time.perf_counter()
            batch_round()
            batch_seconds.append(time.perf_counter() - start)
        scalar_median = statistics.median(scalar_seconds)
        batch_median = statistics.median(batch_seconds)
        self.assertLess(batch_median, scalar_median * 0.95)


if __name__ == "__main__":
    unittest.main(verbosity=2)

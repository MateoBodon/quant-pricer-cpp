#!/usr/bin/env python3
"""Installed-wheel concurrency evaluator for Heston analytic batches."""

from __future__ import annotations

import concurrent.futures
import statistics
import sys
import time
import unittest

import numpy as np
import pyquant_pricer as qp


def make_inputs(count: int, offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    markets = np.empty((count, 5), dtype=np.float64)
    params = np.empty((count, 5), dtype=np.float64)
    for index in range(count):
        point = index + offset
        markets[index] = [
            100.0,
            80.0 + float(point % 41),
            0.015,
            0.005,
            0.25 + 0.25 * float(point % 8),
        ]
        params[index] = [1.5, 0.04, 0.6, -0.45, 0.04]
    return markets, params


def scalar_inputs(
    markets: np.ndarray, params: np.ndarray
) -> list[tuple[object, object]]:
    result: list[tuple[object, object]] = []
    for market_row, param_row in zip(markets, params):
        market = qp.HestonMarket()
        market.spot, market.strike, market.rate, market.dividend, market.time = (
            market_row
        )
        parameter = qp.HestonParams()
        (
            parameter.kappa,
            parameter.theta,
            parameter.sigma,
            parameter.rho,
            parameter.v0,
        ) = param_row
        result.append((market, parameter))
    return result


class PythonHestonAnalyticBatchConcurrencyTest(unittest.TestCase):
    def test_policy_is_process_wide_and_small_batches_are_single_worker(self) -> None:
        self.assertEqual(
            qp.heston_analytic_batch_policy(),
            {"max_process_workers": 4, "items_per_worker": 32},
        )

    def test_concurrent_callers_are_deterministic(self) -> None:
        inputs = [make_inputs(64, offset=1000 * index) for index in range(8)]
        expected = [
            qp.heston_calls_analytic_batch(markets, params)
            for markets, params in inputs
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(qp.heston_calls_analytic_batch, markets, params)
                for markets, params in inputs
            ]
            actual = [future.result(timeout=10.0) for future in futures]
        for concurrent_prices, serial_prices in zip(actual, expected):
            np.testing.assert_array_equal(concurrent_prices, serial_prices)

    def test_size_stratified_performance(self) -> None:
        measurements: dict[int, tuple[float, float]] = {}
        for count in (8, 128):
            markets, params = make_inputs(count)
            objects = scalar_inputs(markets, params)

            def scalar_round() -> None:
                for market, parameter in objects:
                    qp.heston_call_analytic(market, parameter)

            def batch_round() -> None:
                qp.heston_calls_analytic_batch(markets, params)

            scalar_round()
            batch_round()
            scalar_seconds: list[float] = []
            batch_seconds: list[float] = []
            for round_index in range(11):
                ordered = (
                    ((scalar_round, scalar_seconds), (batch_round, batch_seconds))
                    if round_index % 2 == 0
                    else ((batch_round, batch_seconds), (scalar_round, scalar_seconds))
                )
                for function, samples in ordered:
                    start = time.perf_counter()
                    function()
                    samples.append(time.perf_counter() - start)
            measurements[count] = (
                statistics.median(scalar_seconds),
                statistics.median(batch_seconds),
            )
        small_scalar, small_batch = measurements[8]
        large_scalar, large_batch = measurements[128]
        self.assertLess(small_batch, small_scalar * 1.10)
        # Windows process scheduling adds more wall-clock variance than the
        # POSIX runners. Keep a regression guard there without treating this
        # installed-wheel check as a benchmark; artifact-bound performance
        # claims are validated separately on their recorded evaluator.
        large_batch_limit = 1.50 if sys.platform == "win32" else 0.75
        self.assertLess(large_batch, large_scalar * large_batch_limit)


if __name__ == "__main__":
    unittest.main(verbosity=2)

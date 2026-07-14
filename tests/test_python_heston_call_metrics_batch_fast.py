#!/usr/bin/env python3
"""Installed-wheel evaluator for combined analytic Heston call metrics."""

from __future__ import annotations

import concurrent.futures
import statistics
import time
import unittest

import numpy as np
import pyquant_pricer as qp


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


class PythonHestonCallMetricsBatchTest(unittest.TestCase):
    def test_metrics_exactly_match_separate_batches(self) -> None:
        markets, parameter = make_inputs(65)
        metrics = qp.heston_call_metrics_batch(markets, parameter)
        self.assertEqual(metrics.shape, (len(markets), 2))
        self.assertTrue(metrics.flags.c_contiguous)
        np.testing.assert_array_equal(
            metrics[:, 0], qp.heston_calls_analytic_batch(markets, parameter)
        )
        np.testing.assert_array_equal(
            metrics[:, 1], qp.heston_implied_vols_batch(markets, parameter)
        )

    def test_rowwise_parameters_and_validation_share_the_batch_contract(self) -> None:
        markets, parameter = make_inputs(8)
        parameters = np.repeat(parameter, len(markets), axis=0)
        parameters[:, 0] += np.arange(len(markets), dtype=np.float64) * 0.05
        metrics = qp.heston_call_metrics_batch(markets, parameters)
        np.testing.assert_array_equal(
            metrics[:, 0], qp.heston_calls_analytic_batch(markets, parameters)
        )
        np.testing.assert_array_equal(
            metrics[:, 1], qp.heston_implied_vols_batch(markets, parameters)
        )
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_call_metrics_batch(markets, parameters[:2])
        invalid = markets.copy()
        invalid[0, 4] = 0.0
        with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
            qp.heston_call_metrics_batch(invalid, parameter)

    def test_concurrent_callers_are_deterministic_under_shared_policy(self) -> None:
        inputs = [make_inputs(64, offset=1000 * index) for index in range(8)]
        expected = [qp.heston_call_metrics_batch(*item) for item in inputs]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(qp.heston_call_metrics_batch, *item) for item in inputs
            ]
            actual = [future.result(timeout=10.0) for future in futures]
        for concurrent_metrics, serial_metrics in zip(actual, expected):
            np.testing.assert_array_equal(concurrent_metrics, serial_metrics)
        self.assertEqual(
            qp.heston_analytic_batch_policy(),
            {"max_process_workers": 4, "items_per_worker": 32},
        )

    def test_combined_batch_is_faster_than_two_separate_batches(self) -> None:
        markets, parameter = make_inputs(128)

        def combined() -> None:
            qp.heston_call_metrics_batch(markets, parameter)

        def separate() -> None:
            qp.heston_calls_analytic_batch(markets, parameter)
            qp.heston_implied_vols_batch(markets, parameter)

        combined()
        separate()
        combined_seconds: list[float] = []
        separate_seconds: list[float] = []
        for round_index in range(11):
            ordered = (
                ((combined, combined_seconds), (separate, separate_seconds))
                if round_index % 2 == 0
                else ((separate, separate_seconds), (combined, combined_seconds))
            )
            for function, samples in ordered:
                start = time.perf_counter()
                function()
                samples.append(time.perf_counter() - start)
        self.assertLess(
            statistics.median(combined_seconds), statistics.median(separate_seconds)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

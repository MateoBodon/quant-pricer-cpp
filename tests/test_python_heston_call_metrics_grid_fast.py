#!/usr/bin/env python3
"""Installed-wheel evaluator for Cartesian analytic Heston call-metrics grids."""

from __future__ import annotations

import concurrent.futures
import unittest
from pathlib import Path

import numpy as np
import pyquant_pricer as qp


REPO_ROOT = Path(__file__).resolve().parents[1]


def make_inputs(offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    markets = np.array(
        [
            [100.0, 80.0 + offset % 7, 0.005, 0.0, 0.25],
            [100.0, 90.0 + offset % 5, 0.01, 0.0025, 0.5],
            [100.0, 100.0, 0.015, 0.005, 1.0],
            [100.0, 110.0 - offset % 3, 0.02, 0.0075, 1.5],
            [100.0, 120.0, 0.025, 0.01, 2.0],
        ],
        dtype=np.float64,
    )
    parameters = np.array(
        [
            [1.1, 0.035, 0.4, -0.35, 0.03],
            [1.5, 0.04, 0.6, -0.45, 0.04],
            [2.0, 0.05, 0.8, -0.55, 0.06],
            [2.5, 0.06, 1.0, -0.65, 0.08],
        ],
        dtype=np.float64,
    )
    return markets, parameters


class PythonHestonCallMetricsGridTest(unittest.TestCase):
    def test_candidate_major_cells_exactly_match_batch(self) -> None:
        markets, parameters = make_inputs()
        grid = qp.heston_call_metrics_grid(markets, parameters)
        self.assertEqual(grid.shape, (len(parameters), len(markets), 2))
        self.assertTrue(grid.flags.c_contiguous)
        for index, parameter in enumerate(parameters):
            expected = qp.heston_call_metrics_batch(markets, parameter.reshape(1, 5))
            np.testing.assert_array_equal(grid[index], expected)

    def test_validation_and_overflow_guard_precede_allocation(self) -> None:
        markets, parameters = make_inputs()
        with self.assertRaisesRegex(ValueError, "non-empty"):
            qp.heston_call_metrics_grid(np.empty((0, 5)), parameters)
        invalid = parameters.copy()
        invalid[1, 3] = 1.0
        with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
            qp.heston_call_metrics_grid(markets, invalid)
        source = (REPO_ROOT / "python/pybind_module.cpp").read_text(encoding="utf-8")
        guard = source.index("parameter_count > max_items / market_count")
        allocation = source.index("ShapeContainer{parameter_count, market_count")
        self.assertLess(guard, allocation)

    def test_compact_inputs_avoid_cartesian_materialization(self) -> None:
        market_count, parameter_count = 65, 8
        row_bytes = 5 * np.dtype(np.float64).itemsize
        compact_input_bytes = (market_count + parameter_count) * row_bytes
        materialized_input_bytes = 2 * market_count * parameter_count * row_bytes
        self.assertLess(compact_input_bytes * 10, materialized_input_bytes)

    def test_concurrent_grids_are_deterministic_under_shared_policy(self) -> None:
        inputs = [make_inputs(offset=1000 * index) for index in range(8)]
        expected = [qp.heston_call_metrics_grid(*item) for item in inputs]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(qp.heston_call_metrics_grid, *item) for item in inputs]
            actual = [future.result(timeout=10.0) for future in futures]
        for concurrent_grid, serial_grid in zip(actual, expected):
            np.testing.assert_array_equal(concurrent_grid, serial_grid)
        self.assertEqual(
            qp.heston_analytic_batch_policy(),
            {"max_process_workers": 4, "items_per_worker": 32},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

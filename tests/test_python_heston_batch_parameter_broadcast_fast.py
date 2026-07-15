#!/usr/bin/env python3
"""Installed-wheel evaluator for analytic Heston parameter-row broadcasting."""

from __future__ import annotations

import unittest

import numpy as np
import pyquant_pricer as qp


class PythonHestonBatchParameterBroadcastTest(unittest.TestCase):
    def setUp(self) -> None:
        self.markets = np.array(
            [
                [80.0, 95.0, -0.005, 0.01, 0.25],
                [100.0, 100.0, 0.015, 0.005, 1.0],
                [125.0, 105.0, 0.03, 0.0, 2.0],
                [90.0, 115.0, 0.01, 0.02, 0.5],
            ],
            dtype=np.float64,
        )
        self.parameter = np.array([[1.5, 0.04, 0.6, -0.45, 0.04]], dtype=np.float64)

    def test_one_parameter_row_matches_explicit_rows_for_calls_and_puts(self) -> None:
        explicit = np.repeat(self.parameter, len(self.markets), axis=0)
        for batch_pricer in (
            qp.heston_calls_analytic_batch,
            qp.heston_puts_analytic_batch,
        ):
            broadcast = batch_pricer(self.markets, self.parameter)
            rowwise = batch_pricer(self.markets, explicit)
            np.testing.assert_array_equal(broadcast, rowwise)
            self.assertTrue(broadcast.flags.c_contiguous)

    def test_existing_distinct_row_parameters_remain_elementwise(self) -> None:
        explicit = np.repeat(self.parameter, len(self.markets), axis=0)
        explicit[:, 0] += np.arange(len(self.markets), dtype=np.float64) * 0.1
        calls = qp.heston_calls_analytic_batch(self.markets, explicit)
        puts = qp.heston_puts_analytic_batch(self.markets, explicit)
        self.assertEqual(calls.shape, (len(self.markets),))
        self.assertEqual(puts.shape, (len(self.markets),))
        self.assertTrue(np.all(np.isfinite(calls)))
        self.assertTrue(np.all(np.isfinite(puts)))

    def test_other_parameter_row_counts_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_calls_analytic_batch(
                self.markets, np.repeat(self.parameter, 2, axis=0)
            )
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_puts_analytic_batch(
                self.markets, np.repeat(self.parameter, 3, axis=0)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

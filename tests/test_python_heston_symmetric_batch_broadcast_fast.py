#!/usr/bin/env python3
"""Installed-wheel evaluator for symmetric analytic Heston row broadcasting."""

from __future__ import annotations

import unittest

import numpy as np
import pyquant_pricer as qp


class PythonHestonSymmetricBatchBroadcastTest(unittest.TestCase):
    def setUp(self) -> None:
        self.market = np.array([[100.0, 95.0, 0.015, 0.005, 0.75]], dtype=np.float64)
        self.parameters = np.array(
            [
                [1.1, 0.035, 0.4, -0.35, 0.03],
                [1.5, 0.04, 0.6, -0.45, 0.04],
                [2.0, 0.05, 0.8, -0.55, 0.06],
                [2.5, 0.06, 1.0, -0.65, 0.08],
            ],
            dtype=np.float64,
        )
        self.pricers = (
            qp.heston_calls_analytic_batch,
            qp.heston_puts_analytic_batch,
            qp.heston_implied_vols_batch,
            qp.heston_call_metrics_batch,
        )

    def test_one_market_row_matches_explicit_market_rows_for_every_surface(self) -> None:
        explicit_markets = np.repeat(self.market, len(self.parameters), axis=0)
        for pricer in self.pricers:
            broadcast = pricer(self.market, self.parameters)
            explicit = pricer(explicit_markets, self.parameters)
            np.testing.assert_array_equal(broadcast, explicit)
            self.assertTrue(broadcast.flags.c_contiguous)

    def test_one_parameter_row_still_matches_explicit_parameter_rows(self) -> None:
        markets = np.repeat(self.market, len(self.parameters), axis=0)
        markets[:, 1] += np.arange(len(markets), dtype=np.float64) * 5.0
        parameter = self.parameters[1:2]
        explicit_parameters = np.repeat(parameter, len(markets), axis=0)
        for pricer in self.pricers:
            np.testing.assert_array_equal(
                pricer(markets, parameter),
                pricer(markets, explicit_parameters),
            )

    def test_single_pair_shapes_and_other_mismatches(self) -> None:
        for pricer in self.pricers[:-1]:
            self.assertEqual(pricer(self.market, self.parameters[:1]).shape, (1,))
        self.assertEqual(qp.heston_call_metrics_batch(self.market, self.parameters[:1]).shape, (1, 2))
        two_markets = np.repeat(self.market, 2, axis=0)
        three_parameters = self.parameters[:3]
        for pricer in self.pricers:
            with self.assertRaisesRegex(ValueError, "one row or match"):
                pricer(two_markets, three_parameters)

    def test_invalid_broadcast_row_fails_closed(self) -> None:
        invalid_market = self.market.copy()
        invalid_market[0, 0] = 0.0
        for pricer in self.pricers:
            with self.assertRaisesRegex(ValueError, "invalid Heston inputs"):
                pricer(invalid_market, self.parameters)


if __name__ == "__main__":
    unittest.main(verbosity=2)

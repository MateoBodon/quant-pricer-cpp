#!/usr/bin/env python3
"""Executable documentation checks for the analytic Heston batch API."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

import numpy as np
import pyquant_pricer as qp

REPO_ROOT = Path(__file__).resolve().parents[1]
QUICKSTART = REPO_ROOT / "python/examples/quickstart.py"


class PythonHestonBatchDocsTest(unittest.TestCase):
    def test_readme_freezes_columns_and_worker_policy(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("(spot, strike, rate, dividend, time)", readme)
        self.assertIn("(kappa, theta, sigma, rho, v0)", readme)
        self.assertIn("one parameter row", readme)
        self.assertIn("process-wide four-worker budget", readme)
        self.assertIn("heston_analytic_batch_policy", readme)

    def test_quickstart_batch_example_executes(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "quant_pricer_quickstart", QUICKSTART
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            module.price_heston_batch()
        self.assertIn("Heston analytic batch:", output.getvalue())

    def test_documented_validation_is_fail_closed(self) -> None:
        markets = np.array([[100.0, 100.0, 0.01, 0.0, 1.0]])
        params = np.array([[1.5, 0.04, 0.6, -0.45, 0.04]])
        self.assertEqual(qp.heston_calls_analytic_batch(markets, params).shape, (1,))
        self.assertEqual(
            qp.heston_calls_analytic_batch(np.repeat(markets, 2, axis=0), params).shape,
            (2,),
        )
        with self.assertRaisesRegex(ValueError, "one row or match"):
            qp.heston_calls_analytic_batch(
                np.repeat(markets, 3, axis=0), np.repeat(params, 2, axis=0)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

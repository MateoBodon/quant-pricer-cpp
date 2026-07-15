#!/usr/bin/env python3
"""Prove native, module, and distribution version identity."""

from __future__ import annotations

import os
import unittest
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.3.5"


class PythonVersionBindingTest(unittest.TestCase):
    def test_binding_is_derived_from_native_version(self) -> None:
        source = (ROOT / "python/pybind_module.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "quant/version.hpp"', source)
        self.assertIn('m.attr("__version__") = quant::version_string();', source)

    @unittest.skipIf(
        os.environ.get("PYQUANT_SOURCE_ONLY") == "1", "source-only validation"
    )
    def test_installed_module_matches_distribution_metadata(self) -> None:
        import pyquant_pricer as qp

        distribution_version = version("pyquant-pricer")
        self.assertEqual(distribution_version, EXPECTED_VERSION)
        self.assertEqual(qp.__version__, distribution_version)


if __name__ == "__main__":
    unittest.main(verbosity=2)

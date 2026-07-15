#!/usr/bin/env python3
"""Static and executable checks for installed-wheel CI coverage."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "python/scripts/cibw_test_suite.py"


class PythonHestonBatchCiConfigTest(unittest.TestCase):
    def test_all_wheel_jobs_use_the_shared_installed_wheel_suite(self) -> None:
        wheels = (REPO_ROOT / ".github/workflows/wheels.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'CIBW_TEST_COMMAND: python "{project}/python/scripts/cibw_test_suite.py"',
            wheels,
        )
        self.assertIn("os: [ubuntu-latest, macos-latest, windows-latest]", wheels)
        self.assertIn("cp38-* cp39-* cp310-* cp311-* cp312-*", wheels)

    def test_pull_request_ci_builds_and_tests_an_installed_wheel(self) -> None:
        ci = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("python-wheel-smoke:", ci)
        self.assertIn("python -m pip wheel . --no-deps --wheel-dir wheelhouse", ci)
        self.assertIn("python python/scripts/cibw_test_suite.py", ci)

    def test_shared_suite_covers_the_full_batch_contract(self) -> None:
        spec = importlib.util.spec_from_file_location("cibw_test_suite", RUNNER_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module.CHECKS,
            (
                "python/scripts/cibw_smoke.py",
                "tests/test_python_heston_analytic_binding_fast.py",
                "tests/test_python_heston_analytic_batch_fast.py",
                "tests/test_python_heston_analytic_put_batch_fast.py",
                "tests/test_python_heston_analytic_put_fast.py",
                "tests/test_python_heston_batch_parameter_broadcast_fast.py",
                "tests/test_python_heston_implied_vol_batch_fast.py",
                "tests/test_python_heston_call_metrics_batch_fast.py",
                "tests/test_python_heston_symmetric_batch_broadcast_fast.py",
                "tests/test_python_heston_call_metrics_grid_fast.py",
                "tests/test_python_heston_analytic_batch_concurrency_fast.py",
                "tests/test_python_heston_batch_docs_fast.py",
                "tests/test_python_version_binding_fast.py",
            ),
        )
        for relative_path in module.CHECKS:
            self.assertTrue((REPO_ROOT / relative_path).is_file(), relative_path)

    def test_declared_python_floor_matches_the_wheel_suite(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        batch_test = (
            REPO_ROOT / "tests/test_python_heston_analytic_batch_fast.py"
        ).read_text(encoding="utf-8")
        concurrency_test = (
            REPO_ROOT / "tests/test_python_heston_analytic_batch_concurrency_fast.py"
        ).read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.8"', pyproject)
        self.assertNotIn("strict=True", batch_test)
        self.assertNotIn("strict=True", concurrency_test)


if __name__ == "__main__":
    unittest.main(verbosity=2)

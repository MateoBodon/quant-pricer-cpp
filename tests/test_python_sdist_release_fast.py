#!/usr/bin/env python3
"""Focused static tests for the source-distribution release contract."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


class SdistReleaseTest(unittest.TestCase):
    def test_one_sdist_job_builds_validates_and_rebuilds_wheel(self) -> None:
        self.assertEqual(WORKFLOW.count("python -m build --sdist"), 1)
        self.assertIn("python python/scripts/validate_sdist.py dist/*.tar.gz", WORKFLOW)
        self.assertIn("python -m pip wheel dist/*.tar.gz --no-deps", WORKFLOW)
        self.assertIn("python python/scripts/cibw_test_suite.py", WORKFLOW)

    def test_sdist_artifact_is_unique_and_publisher_waits_for_it(self) -> None:
        self.assertEqual(WORKFLOW.count("          name: sdist\n"), 2)
        self.assertIn("needs: [build_wheels, build_sdist]", WORKFLOW)
        self.assertIn("path: dist/*.tar.gz", WORKFLOW)

    def test_single_publisher_merges_wheels_and_sdist(self) -> None:
        self.assertEqual(WORKFLOW.count("twine upload --repository-url"), 1)
        self.assertIn("pattern: wheels-*", WORKFLOW)
        self.assertIn(
            "twine upload --repository-url https://test.pypi.org/legacy/ dist/*",
            WORKFLOW,
        )

    def test_internal_control_and_run_material_is_excluded(self) -> None:
        for path in (
            ".project-os/**",
            "docs/agent_runs/**",
            "project_state/**",
            "reports/**",
        ):
            self.assertIn('"{}"'.format(path), PYPROJECT)


if __name__ == "__main__":
    unittest.main(verbosity=2)

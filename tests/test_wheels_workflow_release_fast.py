#!/usr/bin/env python3
"""Static release-safety checks for the multi-platform wheel workflow."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github/workflows/wheels.yml"


class WheelsWorkflowReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.pre_publish_block, separator, self.publish_block = self.workflow.partition(
            "\n  publish_testpypi:\n"
        )
        self.build_block = self.pre_publish_block.partition("\n  build_sdist:\n")[0]
        self.assertTrue(separator, "publish_testpypi job is missing")

    def test_matrix_artifacts_have_unique_os_scoped_names(self) -> None:
        self.assertIn(
            "os: [ubuntu-latest, macos-latest, windows-latest]", self.build_block
        )
        self.assertIn("name: wheels-${{ matrix.os }}", self.build_block)
        self.assertNotIn("\n          name: wheels\n", self.build_block)

    def test_publish_job_depends_on_complete_matrix_and_merges_artifacts(self) -> None:
        self.assertIn("needs: [build_wheels, build_sdist]", self.publish_block)
        self.assertIn("uses: actions/download-artifact@v4", self.publish_block)
        self.assertIn("pattern: wheels-*", self.publish_block)
        self.assertIn("path: dist", self.publish_block)
        self.assertIn("merge-multiple: true", self.publish_block)

    def test_token_is_publish_only_and_upload_occurs_once(self) -> None:
        self.assertNotIn("TEST_PYPI_API_TOKEN", self.pre_publish_block)
        self.assertIn(
            "TEST_PYPI_API_TOKEN: ${{ secrets.TEST_PYPI_API_TOKEN }}",
            self.publish_block,
        )
        self.assertIn("if: env.TEST_PYPI_API_TOKEN != ''", self.publish_block)
        self.assertEqual(self.workflow.count("twine upload --repository-url"), 1)

    def test_publish_job_uploads_only_merged_release_directory(self) -> None:
        self.assertIn(
            "twine upload --repository-url https://test.pypi.org/legacy/ dist/*",
            self.publish_block,
        )
        self.assertNotIn("twine upload", self.pre_publish_block)


if __name__ == "__main__":
    unittest.main(verbosity=2)

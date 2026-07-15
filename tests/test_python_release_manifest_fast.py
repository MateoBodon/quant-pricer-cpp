#!/usr/bin/env python3
"""Focused tests for deterministic Python release provenance."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "python/scripts/release_manifest.py"
WORKFLOW = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")
SPEC = importlib.util.spec_from_file_location("release_manifest", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseManifestTest(unittest.TestCase):
    def test_manifest_binds_hashes_version_commit_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdist = root / "pyquant_pricer-0.3.7.tar.gz"
            wheel = root / "pyquant_pricer-0.3.7-py3-none-any.whl"
            sdist.write_bytes(b"sdist")
            wheel.write_bytes(b"wheel")
            manifest = MODULE.build_manifest([wheel, sdist], "a" * 40, ROOT, "6.2.0")
        self.assertEqual(manifest["version"], "0.3.7")
        self.assertEqual(manifest["source_commit"], "a" * 40)
        self.assertEqual(
            [item["filename"] for item in manifest["artifacts"]],
            sorted([sdist.name, wheel.name]),
        )
        self.assertTrue(
            all(len(item["sha256"]) == 64 for item in manifest["artifacts"])
        )
        self.assertIn("python_version", manifest["tested_runtime"])
        self.assertIn("system", manifest["tested_runtime"])
        self.assertIn("machine", manifest["tested_runtime"])
        self.assertIn("twine_version", manifest["tested_runtime"])

    def test_manifest_requires_one_sdist_and_at_least_one_wheel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "pyquant_pricer-0.3.7-py3-none-any.whl"
            wheel.write_bytes(b"wheel")
            with self.assertRaisesRegex(ValueError, "exactly one sdist"):
                MODULE.build_manifest([wheel], "b" * 40, ROOT, "6.2.0")

    def test_workflow_emits_separate_manifest_without_publishing_json(self) -> None:
        _, separator, publish = WORKFLOW.partition("\n  publish_testpypi:\n")
        self.assertTrue(separator)
        self.assertIn("python python/scripts/release_manifest.py", publish)
        self.assertIn('source-commit "${GITHUB_SHA}"', publish)
        self.assertIn("dist/*", publish)
        self.assertIn("name: release-manifest", publish)
        self.assertIn("path: release-metadata/release-manifest.json", publish)
        self.assertLess(
            publish.index("python python/scripts/release_manifest.py"),
            publish.index("twine upload"),
        )
        self.assertNotIn("pattern: release-*", WORKFLOW)
        self.assertEqual(WORKFLOW.count("twine upload --repository-url"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

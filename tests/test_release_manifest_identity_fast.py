#!/usr/bin/env python3
"""Focused complete-set identity tests for release provenance."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "python/scripts/release_manifest.py"
SPEC = importlib.util.spec_from_file_location("release_manifest", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def artifact(root: Path, name: str) -> Path:
    path = root / name
    path.write_bytes(name.encode("utf-8"))
    return path


class ReleaseManifestIdentityTest(unittest.TestCase):
    def build(self, paths):
        return MODULE.build_manifest(paths, "a" * 40, ROOT, "6.2.0")

    def test_complete_set_records_parsed_project_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [
                artifact(root, "pyquant_pricer-0.4.0.tar.gz"),
                artifact(
                    root, "pyquant_pricer-0.4.0-cp311-cp311-manylinux_2_28_x86_64.whl"
                ),
                artifact(root, "pyquant_pricer-0.4.0-cp312-cp312-macosx_14_0_arm64.whl"),
            ]
            manifest = self.build(paths)
        self.assertEqual(manifest["project"], "pyquant-pricer")
        self.assertEqual(manifest["version"], "0.4.0")
        self.assertTrue(
            all(item["project"] == "pyquant-pricer" for item in manifest["artifacts"])
        )
        self.assertTrue(
            all(item["version"] == "0.4.0" for item in manifest["artifacts"])
        )

    def test_duplicate_filename_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdist = artifact(root, "pyquant_pricer-0.4.0.tar.gz")
            wheel = artifact(root, "pyquant_pricer-0.4.0-py3-none-any.whl")
            with self.assertRaisesRegex(ValueError, "duplicate artifact filenames"):
                self.build([sdist, wheel, wheel])

    def test_mixed_version_wrong_project_and_malformed_names_are_rejected(self) -> None:
        bad_names = (
            "pyquant_pricer-0.3.2-py3-none-any.whl",
            "other_project-0.4.0-py3-none-any.whl",
            "pyquant_pricer-not-a-wheel.whl",
        )
        for bad_name in bad_names:
            with self.subTest(
                name=bad_name
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                paths = [
                    artifact(root, "pyquant_pricer-0.4.0.tar.gz"),
                    artifact(root, bad_name),
                ]
                with self.assertRaises(ValueError):
                    self.build(paths)

    def test_multiple_sdists_and_missing_wheels_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = artifact(root, "pyquant_pricer-0.4.0.tar.gz")
            second = artifact(root, "pyquant-pricer-0.4.0.tar.gz")
            with self.assertRaisesRegex(ValueError, "exactly one sdist"):
                self.build([first, second])
            with self.assertRaisesRegex(ValueError, "at least one wheel"):
                self.build([first])


if __name__ == "__main__":
    unittest.main(verbosity=2)

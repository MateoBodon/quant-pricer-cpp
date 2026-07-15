#!/usr/bin/env python3
"""Focused executable and workflow checks for release tag/version gating."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "python/scripts/check_release_tag.py"
SPEC = importlib.util.spec_from_file_location("check_release_tag", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseTagVersionGateTest(unittest.TestCase):
    def test_matching_canonical_tag_passes_all_version_surfaces(self) -> None:
        self.assertEqual(MODULE.validate_ref("refs/tags/v0.4.0", ROOT), "0.4.0")
        self.assertEqual(
            MODULE.authoritative_versions(ROOT),
            {
                "cmake": "0.4.0",
                "native": "0.4.0",
                "pyproject": "0.4.0",
                "setup": "0.4.0",
            },
        )

    def test_mismatch_and_malformed_refs_fail_closed(self) -> None:
        for ref in (
            "refs/tags/v0.3.4",
            "refs/tags/v0.3",
            "refs/tags/v00.4.0",
            "refs/tags/v0.4.0-rc1",
            "refs/heads/main",
            "v0.4.0",
            "",
        ):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                MODULE.validate_ref(ref, ROOT)

    def test_every_release_build_graph_depends_on_shared_preflight(self) -> None:
        wheels = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        command = 'python3 python/scripts/check_release_tag.py --ref "${GITHUB_REF}"'
        self.assertEqual(wheels.count(command), 1)
        self.assertEqual(release.count(command), 1)
        self.assertRegex(wheels, r"(?ms)^  build_wheels:\n    needs: preflight$")
        self.assertRegex(wheels, r"(?ms)^  build_sdist:\n    needs: preflight$")
        self.assertIn("needs: [build_wheels, build_sdist]", wheels)
        self.assertRegex(release, r"(?ms)^  build-and-release:\n    needs: preflight$")


if __name__ == "__main__":
    unittest.main(verbosity=2)

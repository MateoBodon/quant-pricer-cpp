#!/usr/bin/env python3
"""Focused consistency checks for the v0.3.4 Python release candidate."""

from __future__ import annotations

import configparser
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.4"


class PythonReleaseCandidateTest(unittest.TestCase):
    def test_authoritative_version_surfaces_match(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        header = (ROOT / "include/quant/version.hpp").read_text(encoding="utf-8")
        setup = configparser.ConfigParser()
        setup.read(ROOT / "setup.cfg", encoding="utf-8")
        self.assertRegex(pyproject, r'(?m)^version = "0\.3\.4"$')
        self.assertRegex(
            cmake, r"(?m)^project\(quant_pricer_cpp VERSION 0\.3\.4 LANGUAGES CXX\)$"
        )
        self.assertRegex(header, r"(?m)^constexpr int kVersionMajor = 0;$")
        self.assertRegex(header, r"(?m)^constexpr int kVersionMinor = 3;$")
        self.assertRegex(header, r"(?m)^constexpr int kVersionPatch = 4;$")
        self.assertEqual(setup["metadata"]["version"], VERSION)

    def test_v033_release_note_covers_shipped_product_and_release_guarantees(
        self,
    ) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.3\.3\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in (
            "heston_calls_analytic_batch",
            "process-wide four-worker budget",
            "installed-wheel contract",
            "source distribution",
            "deterministic manifest",
            "PyPI and TestPyPI availability are not asserted",
        ):
            self.assertIn(required, note)

    def test_v034_note_records_the_wheel_baseline_repair(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.3\.4\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in ("manylinux_2_28", "GCC 10", "cibuildwheel", "unchanged"):
            self.assertIn(required, note)

    def test_reproduction_checks_committed_snapshot_before_regeneration(self) -> None:
        script = (ROOT / "scripts/reproduce_all.sh").read_text(encoding="utf-8")
        committed_check = 'run_py "${ROOT}/tests/test_metrics_snapshot_fast.py"'
        self.assertLess(script.index(committed_check), script.rindex("maybe_clean_artifacts"))
        self.assertIn(
            'run_ctest_label "FAST" -E "^metrics_snapshot_fast$"',
            script,
        )
        self.assertLess(
            script.rindex("finalize_manifest"), script.rindex("generate_metrics_summary")
        )

    def test_existing_v032_note_remains_separate(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLess(changelog.index("## v0.3.3"), changelog.index("## v0.3.2"))
        self.assertEqual(changelog.count("## v0.3.3"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

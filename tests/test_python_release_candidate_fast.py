#!/usr/bin/env python3
"""Focused consistency checks for the v0.4.0 Python release candidate."""

from __future__ import annotations

import configparser
import re
import stat
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.0"


class PythonReleaseCandidateTest(unittest.TestCase):
    def test_authoritative_version_surfaces_match(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        header = (ROOT / "include/quant/version.hpp").read_text(encoding="utf-8")
        setup = configparser.ConfigParser()
        setup.read(ROOT / "setup.cfg", encoding="utf-8")
        self.assertRegex(pyproject, r'(?m)^version = "0\.4\.0"$')
        self.assertRegex(
            cmake, r"(?m)^project\(quant_pricer_cpp VERSION 0\.4\.0 LANGUAGES CXX\)$"
        )
        self.assertRegex(header, r"(?m)^constexpr int kVersionMajor = 0;$")
        self.assertRegex(header, r"(?m)^constexpr int kVersionMinor = 4;$")
        self.assertRegex(header, r"(?m)^constexpr int kVersionPatch = 0;$")
        self.assertEqual(setup["metadata"]["version"], VERSION)

    def test_v040_release_note_covers_shipped_product_and_release_guarantees(
        self,
    ) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.4\.0(?: .*?)?\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in (
            "bs_portfolio_risk",
            "bs_portfolio_scenarios",
            "QuantLib",
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

    def test_v035_preserves_the_declared_python_38_wheel_surface(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.3\.5\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in ("v3.4.1", "Python 3.8", "manylinux_2_28", "unchanged"):
            self.assertIn(required, note)

        wheels = (ROOT / ".github/workflows/wheels.yml").read_text(encoding="utf-8")
        self.assertIn("pypa/cibuildwheel@v3.4.1", wheels)
        self.assertIn("CIBW_BUILD: cp38-* cp39-* cp310-* cp311-* cp312-*", wheels)
        self.assertIn("MACOSX_DEPLOYMENT_TARGET=11.0", wheels)
        reproduce = ROOT / "scripts/reproduce_all.sh"
        self.assertTrue(reproduce.stat().st_mode & stat.S_IXUSR)

    def test_v036_records_non_mutating_snapshot_repair(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.3\.6\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in ("restore", "committed summary bytes", "v0.3.5", "unchanged"):
            self.assertIn(required, note)

    def test_v037_separates_python_and_cpp_install_payloads(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## v0\.3\.7\n(.*?)(?=^## )", changelog)
        self.assertIsNotNone(match)
        note = match.group(1)
        for required in ("python", "cpp", "macOS wheel repair", "unchanged"):
            self.assertIn(required, note)

        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        python_cmake = (ROOT / "python/CMakeLists.txt").read_text(encoding="utf-8")
        root_cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn('install.components = ["python"]', pyproject)
        self.assertEqual(python_cmake.count("COMPONENT python"), 3)
        self.assertGreaterEqual(root_cmake.count("COMPONENT cpp"), 4)

    def test_reproduction_checks_committed_snapshot_before_regeneration(self) -> None:
        script = (ROOT / "scripts/reproduce_all.sh").read_text(encoding="utf-8")
        committed_check = 'run_py "${ROOT}/tests/test_metrics_snapshot_fast.py"'
        self.assertLess(
            script.index(committed_check), script.rindex("maybe_clean_artifacts")
        )
        self.assertIn(
            'run_ctest_label "FAST" -E "^metrics_snapshot_fast$"',
            script,
        )
        self.assertLess(
            script.rindex("finalize_manifest"),
            script.rindex("generate_metrics_summary"),
        )

    def test_existing_v033_note_remains_separate(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLess(changelog.index("## v0.4.0"), changelog.index("## v0.3.3"))
        self.assertEqual(changelog.count("## v0.4.0"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

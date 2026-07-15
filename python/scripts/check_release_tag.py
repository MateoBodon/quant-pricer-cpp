#!/usr/bin/env python3
"""Fail closed unless a release tag matches every authoritative version surface."""

from __future__ import annotations

import argparse
import configparser
import os
import re
from pathlib import Path
from typing import Dict

TAG_RE = re.compile(r"^refs/tags/v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def required_match(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        raise ValueError("{} version is missing or malformed".format(label))
    return match.group(1)


def authoritative_versions(repo_root: Path) -> Dict[str, str]:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    cmake = (repo_root / "CMakeLists.txt").read_text(encoding="utf-8")
    header = (repo_root / "include/quant/version.hpp").read_text(encoding="utf-8")
    setup = configparser.ConfigParser()
    setup.read(repo_root / "setup.cfg", encoding="utf-8")
    native_parts = []
    for part in ("Major", "Minor", "Patch"):
        native_parts.append(
            required_match(
                header,
                r"^constexpr int kVersion{} = ([0-9]+);$".format(part),
                "native {}".format(part.lower()),
            )
        )
    return {
        "cmake": required_match(
            cmake,
            r"^project\(quant_pricer_cpp VERSION ([0-9]+\.[0-9]+\.[0-9]+) LANGUAGES CXX\)$",
            "CMake",
        ),
        "native": ".".join(native_parts),
        "pyproject": required_match(
            pyproject, r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"$', "pyproject"
        ),
        "setup": setup.get("metadata", "version"),
    }


def validate_ref(ref: str, repo_root: Path) -> str:
    tag_match = TAG_RE.fullmatch(ref)
    if tag_match is None:
        raise ValueError(
            "release ref must exactly match refs/tags/vX.Y.Z with canonical integers"
        )
    tag_version = ".".join(tag_match.groups())
    versions = authoritative_versions(repo_root)
    mismatched = {
        name: value for name, value in versions.items() if value != tag_version
    }
    if mismatched:
        details = ", ".join(
            "{}={}".format(name, value) for name, value in sorted(mismatched.items())
        )
        raise ValueError(
            "tag version {} does not match {}".format(tag_version, details)
        )
    return tag_version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    try:
        version = validate_ref(args.ref, repo_root)
    except ValueError as error:
        parser.error(str(error))
    print("release tag/version preflight PASS: {}".format(version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

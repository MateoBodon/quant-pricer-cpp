#!/usr/bin/env python3
"""Validate that a pyquant-pricer sdist is build-complete and release-safe."""

from __future__ import annotations

import sys
import tarfile
from pathlib import Path

REQUIRED = (
    "CMakeLists.txt",
    "pyproject.toml",
    "python/CMakeLists.txt",
    "python/pybind_module.cpp",
    "python/scripts/cibw_test_suite.py",
    "include/quant/heston.hpp",
    "src/heston.cpp",
    "external/pcg/include/pcg_random.hpp",
)
FORBIDDEN_PREFIXES = (
    ".project-os/",
    "artifacts/",
    "docs/agent_runs/",
    "docs/_archive/",
    "project_state/",
    "reports/",
)


def validate(archive: Path) -> None:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getnames()
    if not members:
        raise ValueError("sdist is empty")
    root = members[0].split("/", 1)[0]
    relative = {
        name[len(root) + 1 :]
        for name in members
        if name.startswith(root + "/") and name != root + "/"
    }
    missing = [path for path in REQUIRED if path not in relative]
    forbidden = sorted(
        path
        for path in relative
        if any(
            path == prefix[:-1] or path.startswith(prefix)
            for prefix in FORBIDDEN_PREFIXES
        )
    )
    if missing or forbidden:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if forbidden:
            details.append("forbidden: " + ", ".join(forbidden[:10]))
        raise ValueError("; ".join(details))


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_sdist.py SDIST.tar.gz")
    archive = Path(sys.argv[1])
    validate(archive)
    print("sdist contract PASS: {}".format(archive))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

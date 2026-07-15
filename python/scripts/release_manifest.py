#!/usr/bin/env python3
"""Validate release metadata and emit deterministic local provenance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)

VERSION_RE = re.compile(r"^version\s*=\s*[\"']([^\"']+)[\"']\s*$", re.MULTILINE)
PROJECT_NAME = "pyquant-pricer"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_version(repo_root: Path) -> str:
    match = VERSION_RE.search(
        (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    )
    if match is None:
        raise ValueError("project version is missing from pyproject.toml")
    return match.group(1)


def artifact_record(path: Path, expected_version: str) -> Dict[str, object]:
    try:
        if path.name.endswith(".tar.gz"):
            kind = "sdist"
            parsed_project, parsed_version = parse_sdist_filename(path.name)
        elif path.suffix == ".whl":
            kind = "wheel"
            parsed_project, parsed_version, _, _ = parse_wheel_filename(path.name)
        else:
            raise ValueError("unsupported release artifact: {}".format(path.name))
    except (InvalidSdistFilename, InvalidWheelFilename) as error:
        raise ValueError(
            "malformed release artifact filename: {}".format(path.name)
        ) from error
    normalized_project = str(canonicalize_name(parsed_project))
    if normalized_project != str(canonicalize_name(PROJECT_NAME)):
        raise ValueError(
            "artifact project {} does not match {}: {}".format(
                normalized_project, PROJECT_NAME, path.name
            )
        )
    normalized_version = str(parsed_version)
    if normalized_version != expected_version:
        raise ValueError(
            "artifact version {} does not match {}: {}".format(
                normalized_version, expected_version, path.name
            )
        )
    return {
        "filename": path.name,
        "kind": kind,
        "project": normalized_project,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "version": normalized_version,
    }


def build_manifest(
    paths: List[Path], source_commit: str, repo_root: Path, twine_version: str
) -> Dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be a full lowercase Git SHA-1")
    filenames = [path.name for path in paths]
    if len(filenames) != len(set(filenames)):
        raise ValueError("release set contains duplicate artifact filenames")
    expected_version = project_version(repo_root)
    records = sorted(
        (artifact_record(path, expected_version) for path in paths),
        key=lambda item: item["filename"],
    )
    if [item["kind"] for item in records].count("sdist") != 1:
        raise ValueError("release set must contain exactly one sdist")
    if [item["kind"] for item in records].count("wheel") < 1:
        raise ValueError("release set must contain at least one wheel")
    return {
        "artifacts": records,
        "project": PROJECT_NAME,
        "schema_version": 1,
        "source_commit": source_commit,
        "tested_runtime": {
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "system": platform.system(),
            "twine_version": twine_version,
        },
        "version": expected_version,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    artifacts = [path.resolve() for path in args.artifacts]
    subprocess.run(
        [sys.executable, "-m", "twine", "check"] + [str(path) for path in artifacts],
        check=True,
    )
    repo_root = Path(__file__).resolve().parents[2]
    manifest = build_manifest(
        artifacts, args.source_commit, repo_root, importlib.metadata.version("twine")
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("release manifest PASS: {}".format(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

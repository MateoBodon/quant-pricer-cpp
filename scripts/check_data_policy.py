#!/usr/bin/env python3
"""Guard against committing raw/redistributable market-data artifacts."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

PATTERNS = [
    re.compile(r"strike,.*market_iv"),
    re.compile(r"\bsecid\b"),
    re.compile(r"best_bid|best_ask|best_offer"),
]

DATA_EXTS = {".csv", ".parquet", ".json"}
SYNTHETIC_MARKER = "# SYNTHETIC_DATA"

CODE_DOC_EXTS = {
    ".c",
    ".cc",
    ".cpp",
    ".cmake",
    ".h",
    ".hpp",
    ".md",
    ".mk",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
    ".zsh",
}

DATA_DIR_PREFIXES = (
    "artifacts/",
    "docs/artifacts/",
    "data/",
    "wrds_pipeline/sample_data/",
)
SAMPLE_DATA_PREFIX = "wrds_pipeline/sample_data/"


def _git_tracked_files() -> List[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw = result.stdout.decode("utf-8", errors="ignore")
    return [path for path in raw.split("\0") if path]


def _is_allowed_code_doc(path: str) -> bool:
    return Path(path).suffix in CODE_DOC_EXTS


def _is_guarded_data_file(path: str) -> bool:
    suffix = Path(path).suffix
    if suffix not in DATA_EXTS:
        return False
    return any(path.startswith(prefix) for prefix in DATA_DIR_PREFIXES)


def _requires_synthetic_marker(path: str) -> bool:
    return path.startswith(SAMPLE_DATA_PREFIX) and Path(path).suffix == ".csv"


def _has_synthetic_marker(path: str) -> bool:
    text = Path(path).read_text(errors="ignore")
    for idx, line in enumerate(text.splitlines(), 1):
        if line.strip() == "":
            continue
        return line.startswith(SYNTHETIC_MARKER)
    return False


def _scan_lines(path: str) -> Iterable[Tuple[int, str]]:
    data = Path(path).read_bytes()
    text = data.decode("utf-8", errors="ignore")
    for idx, line in enumerate(text.splitlines(), 1):
        for pattern in PATTERNS:
            if pattern.search(line):
                yield idx, line
                break


def main() -> int:
    violations: List[Tuple[str, int, str]] = []
    for rel_path in _git_tracked_files():
        if _is_allowed_code_doc(rel_path):
            continue
        if not _is_guarded_data_file(rel_path):
            continue
        path = Path(rel_path)
        if not path.exists():
            continue
        if _requires_synthetic_marker(rel_path) and not _has_synthetic_marker(rel_path):
            violations.append(
                (rel_path, 1, f"missing {SYNTHETIC_MARKER} marker")
            )
        for line_no, line in _scan_lines(rel_path):
            violations.append((rel_path, line_no, line))

    if not violations:
        print("[data-policy] OK: no restricted patterns found in tracked data artifacts.")
        return 0

    print("[data-policy] FAIL: restricted patterns found in tracked data artifacts:")
    for rel_path, line_no, line in violations:
        print(f"{rel_path}:{line_no}:{line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

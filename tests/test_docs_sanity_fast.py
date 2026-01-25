#!/usr/bin/env python3
"""FAST test: ensure tracked markdown files avoid conflict markers and scaffolds."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SCAFFOLD_RE = re.compile(r"\(commands\)|\(bullets\)|\(tips\)")
HHMMSS_BAN_PATHS = {
    "PROGRESS.md",
    "docs/RUNBOOK.md",
    "project_state/RUNBOOK.md",
}


def list_tracked_markdown() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_conflict_marker(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith("<<<<<<< ") or stripped.startswith(">>>>>>> "):
        return True
    return stripped.strip() == "======="


def test_docs_sanity_fast() -> None:
    findings: list[str] = []
    for rel_path in list_tracked_markdown():
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if is_conflict_marker(line):
                findings.append(f"{rel_path}:{line_no}: conflict marker: {line.rstrip()}")
                continue
            if SCAFFOLD_RE.search(line):
                findings.append(f"{rel_path}:{line_no}: placeholder: {line.rstrip()}")
            if rel_path in HHMMSS_BAN_PATHS and "HHMMSS" in line:
                findings.append(f"{rel_path}:{line_no}: placeholder: {line.rstrip()}")
    if findings:
        print("Docs sanity violations:")
        for finding in findings:
            print(finding)
        raise AssertionError(
            f"Found {len(findings)} docs sanity violation(s); see output above."
        )


if __name__ == "__main__":
    test_docs_sanity_fast()

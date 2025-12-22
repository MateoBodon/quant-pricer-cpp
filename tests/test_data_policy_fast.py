#!/usr/bin/env python3
"""FAST test: ensure data policy guard passes for tracked artifacts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_data_policy_guard() -> None:
    script = REPO_ROOT / "scripts" / "check_data_policy.py"
    cmd = [sys.executable, str(script)]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


if __name__ == "__main__":
    test_data_policy_guard()

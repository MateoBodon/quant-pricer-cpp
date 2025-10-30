#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "artifacts" / "parity_checks.csv"
    png_path = repo_root / "artifacts" / "parity_checks.png"

    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "parity_checks.py"),
        "--fast",
    ]
    subprocess.check_call(cmd, cwd=repo_root)

    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    if not png_path.exists():
        raise FileNotFoundError(png_path)

    with csv_path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) <= 10:
        raise AssertionError("parity_checks.csv should contain more than 10 rows")


if __name__ == "__main__":
    main()

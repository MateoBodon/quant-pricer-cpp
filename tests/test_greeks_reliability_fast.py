#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "greeks_reliability.py"
    cmd = [
        sys.executable,
        str(script),
        "--fast",
        "--seed",
        "1337",
    ]
    subprocess.check_call(cmd, cwd=repo_root)

    csv_path = repo_root / "artifacts" / "greeks_reliability.csv"
    png_path = repo_root / "artifacts" / "greeks_reliability.png"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    if not png_path.exists():
        raise FileNotFoundError(png_path)

    with csv_path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) <= 5:
        raise AssertionError("Expected >5 rows in greeks_reliability.csv")

    methods = {row["method"] for row in rows}
    required = {"delta_pathwise", "delta_lr", "delta_fd", "gamma_lr", "gamma_fd"}
    missing = required - methods
    if missing:
        raise AssertionError(f"Estimator methods missing from CSV: {sorted(missing)}")


if __name__ == "__main__":
    main()

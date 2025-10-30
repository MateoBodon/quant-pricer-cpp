#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        png_path = tmp_dir / "qmc_plot.png"
        csv_path = tmp_dir / "qmc_summary.csv"
        cmd = [
            sys.executable,
            str(repo_root / "scripts" / "qmc_vs_prng.py"),
            "--fast",
            "--seed",
            "101",
            "--output",
            str(png_path),
            "--csv",
            str(csv_path),
        ]
        subprocess.check_call(cmd, cwd=repo_root)

        if not csv_path.exists():
            raise AssertionError("QMC vs PRNG CSV was not created")
        with csv_path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) <= 5:
            raise AssertionError("Expected >5 rows in QMC vs PRNG CSV")
        required = {"paths", "rmse_prng", "rmse_qmc", "slope_prng", "slope_qmc"}
        missing = required - set(rows[0].keys())
        if missing:
            raise AssertionError(f"Missing columns in QMC vs PRNG CSV: {sorted(missing)}")

    manifest_path = repo_root / "artifacts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    qmc_entry = manifest["runs"].get("qmc_vs_prng")
    if not qmc_entry:
        raise AssertionError("Manifest missing qmc_vs_prng entry")
    seed = qmc_entry.get("seed")
    if seed != 101:
        raise AssertionError(f"Expected qmc_vs_prng seed 101, found {seed}")
    if qmc_entry.get("csv_rows", 0) <= 5:
        raise AssertionError("Manifest qmc_vs_prng entry reports insufficient csv_rows")
    if "command" not in qmc_entry:
        raise AssertionError("Manifest qmc_vs_prng entry missing command")


if __name__ == "__main__":
    main()

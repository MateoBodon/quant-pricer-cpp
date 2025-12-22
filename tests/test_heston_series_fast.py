#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "heston_series_plot.py"
    inputs = [
        repo_root / "data" / "normalized" / "spy_20230601.csv",
        repo_root / "data" / "samples" / "spx_20240614_sample.csv",
    ]
    for path in inputs:
        if not path.exists():
            raise FileNotFoundError(path)
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "heston"
        csv_path = out_dir / "params_series.csv"
        png_path = out_dir / "params_series.png"
        cmd = [
            sys.executable,
            str(script),
            "--inputs",
            str(inputs[0]),
            str(inputs[1]),
            "--metric",
            "price",
            "--fast",
            "--seed",
            "23",
            "--retries",
            "2",
            "--output-csv",
            str(csv_path),
            "--output-png",
            str(png_path),
            "--skip-manifest",
        ]
        subprocess.check_call(cmd, cwd=repo_root)

        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        if not png_path.exists():
            raise FileNotFoundError(png_path)

        with csv_path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) < 2:
            raise AssertionError(
                "Heston params_series.csv should contain at least two dates"
            )

        columns = rows[0].keys()
        required_cols = {"date", "kappa", "theta", "sigma_v", "rho", "v0", "rmspe_vol_pct"}
        missing = required_cols - set(columns)
        if missing:
            raise AssertionError(f"Missing columns in params_series.csv: {sorted(missing)}")


if __name__ == "__main__":
    main()

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
    sample = repo_root / "data" / "samples" / "spx_20240614_sample.csv"
    if not sample.exists():
        raise FileNotFoundError(sample)

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        cmd = [
            sys.executable,
            str(repo_root / "scripts" / "calibrate_heston.py"),
            "--input",
            str(sample),
            "--fast",
            "--metric",
            "vol",
            "--seed",
            "17",
            "--retries",
            "3",
            "--output-dir",
            str(out_dir),
        ]
        subprocess.check_call(cmd, cwd=repo_root)

        json_files = sorted(out_dir.glob("params_*.json"))
        if not json_files:
            raise RuntimeError("Calibration did not emit params_*.json")
        data = json.loads(json_files[0].read_text())
        rmse_vol = float(data["rmse_vol"])
        threshold = 0.25
        print(f"rmse_vol={rmse_vol:.4f} (threshold {threshold})")
        if rmse_vol >= threshold:
            raise AssertionError(f"FAST calibration rmse_vol {rmse_vol:.4f} exceeds {threshold}")

        csv_files = sorted(out_dir.glob("fit_*.csv"))
        if not csv_files:
            raise RuntimeError("Calibration did not emit fit_*.csv")
        csv_path = csv_files[0]
        with csv_path.open(newline="") as fh:
            reader = list(csv.DictReader(fh))
        if len(reader) <= 5:
            raise AssertionError("Expected >5 rows in Heston fit CSV")
        required_cols = {"strike", "ttm", "market_iv", "model_iv", "abs_error"}
        missing = required_cols - set(reader[0].keys())
        if missing:
            raise AssertionError(f"Missing columns in Heston fit CSV: {sorted(missing)}")

    manifest_path = repo_root / "artifacts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for key in ["git", "system", "omp_threads", "build", "runs"]:
        if key not in manifest:
            raise AssertionError(f"Manifest missing key '{key}'")
    if not manifest["git"].get("sha"):
        raise AssertionError("Manifest git.sha is missing")
    if not manifest["system"].get("cpu_brand"):
        raise AssertionError("Manifest system.cpu_brand is missing")
    build = manifest["build"]
    if build.get("available") and "cxx_flags" not in build:
        raise AssertionError("Manifest build info missing compiler flags")

    runs = manifest["runs"].get("heston")
    if not runs:
        raise AssertionError("Manifest missing heston run entry")
    latest = runs[-1]
    if latest.get("seed") != 17:
        raise AssertionError("Manifest heston entry missing seed 17")
    if "rmspe_vol_pct" not in latest:
        raise AssertionError("Manifest heston entry missing rmspe_vol_pct")
    inputs = latest.get("inputs", [])
    if not inputs or not inputs[0].get("sha256"):
        raise AssertionError("Manifest heston entry missing input SHA256")


if __name__ == "__main__":
    main()

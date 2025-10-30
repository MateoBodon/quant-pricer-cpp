#!/usr/bin/env python3
from __future__ import annotations

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
            "--skip-manifest",
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


if __name__ == "__main__":
    main()

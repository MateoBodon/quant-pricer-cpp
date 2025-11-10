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
            "price",
            "--weight",
            "vega",
            "--param-transform",
            "exp",
            "--feller-warn",
            "--seed",
            "19",
            "--retries",
            "2",
            "--output-dir",
            str(out_dir),
        ]
        subprocess.check_call(cmd, cwd=repo_root)

    manifest_path = repo_root / "docs" / "artifacts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    runs = manifest.get("runs", {}).get("heston")
    if not runs:
        raise AssertionError("Manifest missing heston runs after safety test")
    latest = runs[-1]
    if latest.get("param_transform") != "exp":
        raise AssertionError("Safety test expected param_transform 'exp'")
    if latest.get("weight_mode") != "vega":
        raise AssertionError("Safety test expected weight_mode 'vega'")
    diagnostics = latest.get("diagnostics", {})
    if "retry_failures" not in diagnostics:
        raise AssertionError("Diagnostics missing retry_failures")
    if "warnings" not in latest:
        raise AssertionError("Manifest entry missing warnings field")


if __name__ == "__main__":
    main()

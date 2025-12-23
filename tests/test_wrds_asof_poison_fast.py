#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run_poison(sample_path: Path, expected_context: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["WRDS_USE_SAMPLE"] = "1"
    env["WRDS_SAMPLE_PATH"] = str(sample_path)
    cmd = [
        sys.executable,
        "-m",
        "wrds_pipeline.pipeline",
        "--fast",
        "--trade-date",
        "2024-06-14",
    ]
    proc = subprocess.run(
        cmd, cwd=repo_root, env=env, capture_output=True, text=True
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        raise AssertionError("Expected WRDS pipeline to fail on poison sample input.")
    needle = f"as-of check failed ({expected_context})"
    if needle not in output:
        tail = output.strip().splitlines()[-12:]
        raise AssertionError(
            f"Expected '{needle}' in output. Tail:\n" + "\n".join(tail)
        )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _run_poison(
        repo_root
        / "wrds_pipeline"
        / "sample_data"
        / "spx_options_sample_poison_calib.csv",
        "calibration",
    )
    _run_poison(
        repo_root
        / "wrds_pipeline"
        / "sample_data"
        / "spx_options_sample_poison_oos.csv",
        "oos",
    )


if __name__ == "__main__":
    main()

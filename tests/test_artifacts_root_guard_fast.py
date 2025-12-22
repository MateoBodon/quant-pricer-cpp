#!/usr/bin/env python3
"""FAST guard: ensure reproduce_all inputs don't emit files under artifacts/."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def _snapshot_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
    }


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.check_call(cmd, cwd=cwd)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_root = repo_root / "artifacts"
    before = _snapshot_files(artifacts_root)

    inputs = [
        repo_root / "data" / "normalized" / "spy_20230601.csv",
        repo_root / "data" / "samples" / "spx_20240614_sample.csv",
    ]
    for path in inputs:
        if not path.exists():
            raise FileNotFoundError(path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "parity_checks.py"),
                "--fast",
                "--output-csv",
                str(tmp_dir / "parity_checks.csv"),
                "--output-png",
                str(tmp_dir / "parity_checks.png"),
                "--skip-manifest",
            ],
            repo_root,
        )

        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "greeks_reliability.py"),
                "--fast",
                "--seed",
                "1337",
                "--output-csv",
                str(tmp_dir / "greeks_reliability.csv"),
                "--output-png",
                str(tmp_dir / "greeks_reliability.png"),
                "--skip-manifest",
            ],
            repo_root,
        )

        heston_dir = tmp_dir / "heston"
        _run(
            [
                sys.executable,
                str(repo_root / "scripts" / "heston_series_plot.py"),
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
                str(heston_dir / "params_series.csv"),
                "--output-png",
                str(heston_dir / "params_series.png"),
                "--skip-manifest",
            ],
            repo_root,
        )

    after = _snapshot_files(artifacts_root)
    new_files = sorted(after - before)
    if new_files:
        sample = ", ".join(new_files[:10])
        suffix = "" if len(new_files) <= 10 else f" (+{len(new_files) - 10} more)"
        raise AssertionError(
            f"Artifacts guard failed: new files under artifacts/: {sample}{suffix}"
        )


if __name__ == "__main__":
    main()

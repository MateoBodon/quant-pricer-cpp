#!/usr/bin/env python3
"""MARKET test wrapper for the WRDS pipeline."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SKIP_CODE = 77


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _has_wrds_env() -> bool:
    return (
        os.environ.get("WRDS_ENABLED") == "1"
        and bool(os.environ.get("WRDS_USERNAME"))
        and bool(os.environ.get("WRDS_PASSWORD"))
    )


def _expected_artifacts(root: Path) -> list[Path]:
    base = root / "docs" / "artifacts" / "wrds"
    return [
        base / "wrds_agg_pricing.csv",
        base / "wrds_agg_oos.csv",
        base / "wrds_agg_pnl.csv",
        base / "wrds_multi_date_summary.png",
    ]


def main() -> None:
    repo_root = _root()
    if not _has_wrds_env():
        print("SKIP: WRDS pipeline disabled (set WRDS_ENABLED=1 with WRDS_USERNAME/WRDS_PASSWORD).")
        raise SystemExit(SKIP_CODE)

    cmd = [sys.executable, str(repo_root / "wrds_pipeline" / "pipeline.py")]
    env = os.environ.copy()
    subprocess.run(cmd, check=True, cwd=repo_root, env=env)

    missing = [path for path in _expected_artifacts(repo_root) if not path.exists()]
    if missing:
        raise SystemExit(f"Missing WRDS artifacts: {', '.join(str(path) for path in missing)}")
    print("WRDS pipeline artifacts ready.")


if __name__ == "__main__":
    main()

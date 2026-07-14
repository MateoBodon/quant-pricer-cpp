#!/usr/bin/env python3
"""Run the installed-wheel contract used by cibuildwheel and pull-request CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    "python/scripts/cibw_smoke.py",
    "tests/test_python_heston_analytic_binding_fast.py",
    "tests/test_python_heston_analytic_batch_fast.py",
    "tests/test_python_heston_analytic_put_batch_fast.py",
    "tests/test_python_heston_analytic_put_fast.py",
    "tests/test_python_heston_batch_parameter_broadcast_fast.py",
    "tests/test_python_heston_implied_vol_batch_fast.py",
    "tests/test_python_heston_call_metrics_batch_fast.py",
    "tests/test_python_heston_symmetric_batch_broadcast_fast.py",
    "tests/test_python_heston_call_metrics_grid_fast.py",
    "tests/test_python_heston_analytic_batch_concurrency_fast.py",
    "tests/test_python_heston_batch_docs_fast.py",
    "tests/test_python_version_binding_fast.py",
)


def main() -> int:
    for relative_path in CHECKS:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / relative_path)],
            cwd=REPO_ROOT,
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

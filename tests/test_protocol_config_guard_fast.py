#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_GRID = REPO_ROOT / "configs" / "scenario_grids" / "synthetic_validation_v1.json"
TOLERANCES = REPO_ROOT / "configs" / "tolerances" / "synthetic_validation_v1.json"
MISSING_MSG = "missing protocol config provenance"


def _find_quant_cli() -> Path:
    candidates = [
        REPO_ROOT / "build" / "quant_cli",
        REPO_ROOT / "build" / "Release" / "quant_cli",
        REPO_ROOT / "build" / "RelWithDebInfo" / "quant_cli",
        REPO_ROOT / "build" / "Debug" / "quant_cli",
        REPO_ROOT / "build" / "quant_cli.exe",
        REPO_ROOT / "build" / "Release" / "quant_cli.exe",
        REPO_ROOT / "quant_cli",
        REPO_ROOT / "quant_cli.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("quant_cli not found; build the project first")


def _expect_missing_provenance(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode == 0:
        raise AssertionError("expected failure without protocol configs")
    output = f"{proc.stdout}\n{proc.stderr}".lower()
    if MISSING_MSG not in output:
        raise AssertionError(
            f"expected '{MISSING_MSG}' in stderr/stdout; got: {output.strip()}"
        )


def _expect_success(cmd: list[str], outputs: list[Path]) -> None:
    subprocess.check_call(cmd, cwd=REPO_ROOT)
    for path in outputs:
        if not path.exists():
            raise AssertionError(f"expected output {path} to exist")


def main() -> None:
    if not SCENARIO_GRID.exists():
        raise AssertionError(f"missing scenario grid: {SCENARIO_GRID}")
    if not TOLERANCES.exists():
        raise AssertionError(f"missing tolerances config: {TOLERANCES}")

    quant_cli = _find_quant_cli()
    tri_script = REPO_ROOT / "scripts" / "tri_engine_agreement.py"
    pde_script = REPO_ROOT / "scripts" / "pde_order_slope.py"
    greeks_script = REPO_ROOT / "scripts" / "mc_greeks_ci.py"
    ql_script = REPO_ROOT / "scripts" / "ql_parity.py"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tri_png = tmp_dir / "tri.png"
        tri_csv = tmp_dir / "tri.csv"
        pde_png = tmp_dir / "pde.png"
        pde_csv = tmp_dir / "pde.csv"
        greek_png = tmp_dir / "greeks.png"
        greek_csv = tmp_dir / "greeks.csv"
        ql_png = tmp_dir / "ql.png"
        ql_csv = tmp_dir / "ql.csv"

        _expect_missing_provenance(
            [
                sys.executable,
                str(tri_script),
                "--quant-cli",
                str(quant_cli),
                "--fast",
                "--output",
                str(tri_png),
                "--csv",
                str(tri_csv),
            ]
        )
        _expect_missing_provenance(
            [
                sys.executable,
                str(pde_script),
                "--skip-build",
                "--fast",
                "--output",
                str(pde_png),
                "--csv",
                str(pde_csv),
            ]
        )
        _expect_missing_provenance(
            [
                sys.executable,
                str(greeks_script),
                "--quant-cli",
                str(quant_cli),
                "--fast",
                "--output",
                str(greek_png),
                "--csv",
                str(greek_csv),
            ]
        )
        _expect_missing_provenance(
            [
                sys.executable,
                str(ql_script),
                "--fast",
                "--output",
                str(ql_png),
                "--csv",
                str(ql_csv),
            ]
        )

        _expect_success(
            [
                sys.executable,
                str(tri_script),
                "--quant-cli",
                str(quant_cli),
                "--scenario-grid",
                str(SCENARIO_GRID),
                "--tolerances",
                str(TOLERANCES),
                "--fast",
                "--output",
                str(tri_png),
                "--csv",
                str(tri_csv),
            ],
            [tri_png, tri_csv],
        )
        _expect_success(
            [
                sys.executable,
                str(pde_script),
                "--skip-build",
                "--scenario-grid",
                str(SCENARIO_GRID),
                "--tolerances",
                str(TOLERANCES),
                "--fast",
                "--output",
                str(pde_png),
                "--csv",
                str(pde_csv),
            ],
            [pde_png, pde_csv],
        )
        _expect_success(
            [
                sys.executable,
                str(greeks_script),
                "--quant-cli",
                str(quant_cli),
                "--scenario-grid",
                str(SCENARIO_GRID),
                "--tolerances",
                str(TOLERANCES),
                "--fast",
                "--output",
                str(greek_png),
                "--csv",
                str(greek_csv),
            ],
            [greek_png, greek_csv],
        )
        _expect_success(
            [
                sys.executable,
                str(ql_script),
                "--scenario-grid",
                str(SCENARIO_GRID),
                "--tolerances",
                str(TOLERANCES),
                "--fast",
                "--output",
                str(ql_png),
                "--csv",
                str(ql_csv),
            ],
            [ql_png, ql_csv],
        )


if __name__ == "__main__":
    main()

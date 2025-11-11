#!/usr/bin/env python3
"""
Compare Heston QE Monte Carlo against the analytic solution and emit CSV/PNG artifacts.
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, update_run


def _find_quant_cli(override: str | None) -> Path:
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path
        raise SystemExit(f"quant_cli not found at {path}")
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "build" / "quant_cli",
        root / "build" / "Release" / "quant_cli",
        root / "build" / "RelWithDebInfo" / "quant_cli",
        root / "build" / "Debug" / "quant_cli",
        root / "build" / "quant_cli.exe",
        root / "build" / "Release" / "quant_cli.exe",
        root / "quant_cli",
        root / "quant_cli.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit("quant_cli executable not found; pass --quant-cli")


def _run_cli_json(cli: Path, args: List[Any]) -> Dict[str, Any]:
    cmd = [str(cli), *[str(arg) for arg in args]]
    output = subprocess.check_output(cmd, text=True)
    return json.loads(output)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quant-cli", help="Path to quant_cli executable")
    ap.add_argument(
        "--paths", type=int, default=80_000, help="Monte Carlo paths per run"
    )
    ap.add_argument("--seed", type=int, default=2025, help="RNG seed")
    ap.add_argument(
        "--fast", action="store_true", help="Skip the largest timestep for CI pipelines"
    )
    ap.add_argument(
        "--output",
        default=str(ARTIFACTS_ROOT / "heston_qe_vs_analytic.png"),
        help="Figure output path",
    )
    ap.add_argument(
        "--csv",
        default=str(ARTIFACTS_ROOT / "heston_qe_vs_analytic.csv"),
        help="CSV output path",
    )
    args = ap.parse_args()

    cli = _find_quant_cli(args.quant_cli)
    paths = max(20_000, args.paths // 2 if args.fast else args.paths)
    step_grid = [16, 32, 64, 128]
    if args.fast and len(step_grid) > 3:
        step_grid = step_grid[:-1]

    heston = {
        "kappa": 1.5,
        "theta": 0.04,
        "sigma": 0.5,
        "rho": -0.5,
        "v0": 0.04,
    }
    market = {
        "spot": 100.0,
        "strike": 100.0,
        "rate": 0.01,
        "dividend": 0.0,
        "tenor": 1.0,
    }

    def make_cli_args(step_count: int) -> List[Any]:
        return [
            "heston",
            heston["kappa"],
            heston["theta"],
            heston["sigma"],
            heston["rho"],
            heston["v0"],
            market["spot"],
            market["strike"],
            market["rate"],
            market["dividend"],
            market["tenor"],
            paths,
            step_count,
            args.seed,
        ]

    analytic_json = _run_cli_json(cli, [*make_cli_args(step_grid[-1]), "--json"])
    analytic_price = float(analytic_json.get("price", math.nan))

    results = []
    commands: List[str] = []
    for scheme_flag, label in (("--heston-qe", "qe"), ("--heston-euler", "euler")):
        for steps in step_grid:
            cmd = [
                *make_cli_args(steps),
                "--mc",
                "--json",
                scheme_flag,
                "--rng=counter",
            ]
            res = _run_cli_json(cli, cmd)
            price = float(res.get("price", math.nan))
            std_error = float(res.get("std_error", math.nan))
            ci_low = float(res.get("ci_low", price))
            ci_high = float(res.get("ci_high", price))
            abs_err = abs(price - analytic_price)
            results.append(
                {
                    "scheme": label,
                    "steps": steps,
                    "paths": paths,
                    "price": price,
                    "std_error": std_error,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "abs_error": abs_err,
                }
            )
            commands.append(shlex.join([str(cli), *[str(arg) for arg in cmd]]))

    df = pd.DataFrame(results).sort_values(["scheme", "steps"])
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.8f")

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for scheme, group in df.groupby("scheme"):
        ax.loglog(group["steps"], group["abs_error"], marker="o", label=scheme.upper())
    ax.set_xlabel("Time steps")
    ax.set_ylabel("|MC price - analytic|")
    ax.set_title(f"Heston QE vs analytic (paths={paths:,}, seed={args.seed})")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    payload = {
        "paths": paths,
        "seed": args.seed,
        "step_grid": step_grid,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "analytic": analytic_price,
        "commands": commands,
        "results": results,
    }
    update_run("heston_qe_vs_analytic", payload)

    print(f"Wrote {csv_path}")
    print(f"Wrote {fig_path}")


if __name__ == "__main__":
    main()

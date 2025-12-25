#!/usr/bin/env python3
"""
Generate PDE grid convergence diagnostics (second-order slope) for a vanilla call.

Outputs:
  * artifacts/pde_order_slope.csv
  * artifacts/pde_order_slope.png
"""
from __future__ import annotations

import argparse
import math
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run
from protocol_utils import (
    load_protocol_configs,
    record_protocol_manifest,
    select_grid_block,
)


def run(cmd: List[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def black_scholes_call(
    S: float, K: float, r: float, q: float, sigma: float, T: float
) -> float:
    if T <= 0:
        return max(S - K, 0.0)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return S * math.exp(-q * T) * nd1 - K * math.exp(-r * T) * nd2


def ensure_build(root: Path, build_dir: Path, skip: bool) -> Path:
    quant_cli = build_dir / "quant_cli"
    if quant_cli.exists() or skip:
        return quant_cli
    build_dir.mkdir(parents=True, exist_ok=True)
    run(["cmake", "-S", str(root), "-B", str(build_dir), "-DCMAKE_BUILD_TYPE=Release"])
    run(["cmake", "--build", str(build_dir), "-j"])
    return quant_cli


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="Use fewer grid nodes for CI")
    ap.add_argument(
        "--skip-build", action="store_true", help="Assume quant_cli is already built"
    )
    ap.add_argument(
        "--scenario-grid", type=Path, help="Path to frozen scenario grid JSON"
    )
    ap.add_argument(
        "--tolerances", type=Path, help="Path to frozen tolerance JSON"
    )
    ap.add_argument(
        "--output", default=str(ARTIFACTS_ROOT / "pde_order_slope.png")
    )
    ap.add_argument(
        "--csv", default=str(ARTIFACTS_ROOT / "pde_order_slope.csv")
    )
    args = ap.parse_args()

    scenario_config, tolerance_config, provenance = load_protocol_configs(
        args.scenario_grid, args.tolerances
    )
    protocol_entry = record_protocol_manifest(
        scenario_config, tolerance_config, provenance
    )
    grid = select_grid_block(scenario_config, "pde_order_slope", args.fast)

    root = Path(__file__).resolve().parents[1]
    build_dir = root / "build"
    quant_cli = ensure_build(root, build_dir, args.skip_build)

    S = float(grid["spot"])
    K = float(grid["strike"])
    r = float(grid["rate"])
    q = float(grid["dividend"])
    sigma = float(grid["vol"])
    T = float(grid["tenor"])
    smax_mult = float(grid.get("smax_mult", 4.0))
    logspace = int(grid.get("logspace", 1))
    neumann = int(grid.get("neumann", 1))
    analytic = black_scholes_call(S, K, r, q, sigma, T)

    grid_nodes = list(grid["grid_nodes"])

    records = []
    for M in grid_nodes:
        N = M - 1
        cmd = [
            str(quant_cli),
            "pde",
            str(S),
            str(K),
            str(r),
            str(q),
            str(sigma),
            str(T),
            "call",
            str(M),
            str(N),
            str(smax_mult),
            str(logspace),
            str(neumann),
        ]
        out = run(cmd)
        price = float(out.split()[0])
        error = abs(price - analytic)
        records.append(
            {
                "nodes": M,
                "timesteps": N,
                "price": price,
                "abs_error": error,
            }
        )

    df = pd.DataFrame(records)
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    x = np.log(df["nodes"].to_numpy())
    y = np.log(df["abs_error"].to_numpy())
    slope, intercept = np.polyfit(x, y, 1)

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(df["nodes"], df["abs_error"], "o-", color="#1f77b4")
    ax.set_xlabel("Spatial Nodes")
    ax.set_ylabel("|Price - Analytic|")
    ax.set_title("PDE Grid Convergence (2nd-order slope)")
    ax.grid(True, which="both", ls=":", alpha=0.5)
    ax.text(0.05, 0.1, f"Slope ≈ {slope:.2f}", transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    tol = tolerance_config.get("pde_order_slope", {})
    slope_ok = None
    if "slope_min" in tol and "slope_max" in tol:
        slope_ok = float(tol["slope_min"]) <= float(slope) <= float(tol["slope_max"])

    payload = {
        "command": shlex.join([sys.executable] + sys.argv),
        "fast": bool(args.fast),
        "nodes": grid_nodes,
        "slope": float(slope),
        "intercept": float(intercept),
        "csv": str(csv_path),
        "figure": str(fig_path),
        "spot": S,
        "strike": K,
        "rate": r,
        "dividend": q,
        "vol": sigma,
        "tenor": T,
        "smax_mult": smax_mult,
        "logspace": logspace,
        "neumann": neumann,
        "analytic": analytic,
        "records": records,
        "protocol": protocol_entry,
        "tolerances": tol,
        "tolerance_checks": {"slope_in_band": slope_ok},
        "inputs": describe_inputs([quant_cli, args.scenario_grid, args.tolerances]),
    }
    update_run("pde_order_slope", payload)

    print(f"Wrote {fig_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()

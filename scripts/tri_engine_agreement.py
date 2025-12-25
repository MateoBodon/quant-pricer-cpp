#!/usr/bin/env python3
"""
Generate the "Tri-Engine Agreement" diagnostic:
analytic Black–Scholes vs Monte Carlo vs PDE across strikes.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run
from protocol_utils import (
    load_protocol_configs,
    record_protocol_manifest,
    select_grid_block,
)


def _bs_call(S: float, K: float, r: float, q: float, sigma: float, T: float) -> float:
    if T <= 0.0:
        return max(S - K, 0.0)
    if sigma <= 0.0:
        disc = math.exp(-r * T)
        fwd = S * math.exp((r - q) * T)
        return disc * max(fwd - K, 0.0)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return S * math.exp(-q * T) * nd1 - K * math.exp(-r * T) * nd2


def _run(cmd: List[str]) -> dict:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out.strip())


def _mc_price(
    quant_cli: str,
    spot: float,
    strike: float,
    r: float,
    q: float,
    sigma: float,
    T: float,
    paths: int,
    seed: int,
    steps: int,
) -> Tuple[float, float]:
    cmd = [
        quant_cli,
        "mc",
        str(spot),
        str(strike),
        str(r),
        str(q),
        str(sigma),
        str(T),
        str(paths),
        str(seed),
        "1",  # antithetic
        "0",  # qmc none
        "bb",
        str(steps),
        "--rng=counter",
        "--ci",
        "--json",
    ]
    res = _run(cmd)
    return float(res["price"]), float(res["std_error"])


def _pde_price(
    quant_cli: str,
    spot: float,
    strike: float,
    r: float,
    q: float,
    sigma: float,
    T: float,
    nodes: int,
    timesteps: int,
) -> float:
    cmd = [
        quant_cli,
        "pde",
        str(spot),
        str(strike),
        str(r),
        str(q),
        str(sigma),
        str(T),
        "call",
        str(nodes),
        str(timesteps),
        "4.5",
        "1",  # log-space
        "1",  # neumann upper boundary
        "2.0",  # stretch
        "1",  # compute theta
        "1",  # rannacher
        "--json",
    ]
    res = _run(cmd)
    return float(res["price"])


def build_dataset(
    quant_cli: str,
    strikes: Iterable[float],
    spot: float,
    r: float,
    q: float,
    sigma: float,
    T: float,
    paths: int,
    seed: int,
    steps: int,
    nodes: int,
) -> pd.DataFrame:
    rows = []
    for strike in strikes:
        bs_price = _bs_call(spot, strike, r, q, sigma, T)
        mc_price, mc_se = _mc_price(
            quant_cli, spot, strike, r, q, sigma, T, paths, seed, steps
        )
        pde_price = _pde_price(
            quant_cli, spot, strike, r, q, sigma, T, nodes, nodes - 1
        )
        rows.append(
            {
                "strike": strike,
                "bs_price": bs_price,
                "mc_price": mc_price,
                "mc_std_error": mc_se,
                "pde_price": pde_price,
                "mc_abs_error": abs(mc_price - bs_price),
                "pde_abs_error": abs(pde_price - bs_price),
            }
        )
    return pd.DataFrame(rows)


def plot(df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 6.5), sharex=True)
    axes[0].plot(
        df["strike"],
        df["bs_price"],
        label="Analytic (BS)",
        color="#2ca02c",
        linewidth=2,
    )
    axes[0].plot(
        df["strike"], df["mc_price"], "o-", label="Monte Carlo", color="#1f77b4"
    )
    axes[0].plot(
        df["strike"], df["pde_price"], "s--", label="PDE (CN)", color="#ff7f0e"
    )
    axes[0].set_ylabel("Call price")
    axes[0].grid(True, ls=":", alpha=0.4)
    axes[0].legend()

    axes[1].semilogy(
        df["strike"], df["mc_abs_error"], "o-", color="#1f77b4", label="|MC - BS|"
    )
    axes[1].semilogy(
        df["strike"], df["pde_abs_error"], "s--", color="#ff7f0e", label="|PDE - BS|"
    )
    axes[1].set_xlabel("Strike")
    axes[1].set_ylabel("Absolute error")
    axes[1].grid(True, which="both", ls=":", alpha=0.4)
    axes[1].legend()

    max_mc = df["mc_abs_error"].max()
    max_pde = df["pde_abs_error"].max()
    axes[1].text(
        0.02,
        0.85,
        f"max |MC-BS| = {max_mc:.4f}\nmax |PDE-BS| = {max_pde:.4f}",
        transform=axes[1].transAxes,
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
    )

    fig.suptitle("Tri-Engine Agreement (Analytic vs MC vs PDE)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quant-cli", required=True, help="Path to quant_cli executable")
    ap.add_argument(
        "--scenario-grid", type=Path, help="Path to frozen scenario grid JSON"
    )
    ap.add_argument(
        "--tolerances", type=Path, help="Path to frozen tolerance JSON"
    )
    ap.add_argument(
        "--output", type=Path, default=ARTIFACTS_ROOT / "tri_engine_agreement.png"
    )
    ap.add_argument(
        "--csv", type=Path, default=ARTIFACTS_ROOT / "tri_engine_agreement.csv"
    )
    ap.add_argument(
        "--fast", action="store_true", help="Reduce paths/grid for CI runtime"
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    if not Path(args.quant_cli).exists():
        raise FileNotFoundError(args.quant_cli)

    scenario_config, tolerance_config, provenance = load_protocol_configs(
        args.scenario_grid, args.tolerances
    )
    protocol_entry = record_protocol_manifest(
        scenario_config, tolerance_config, provenance
    )
    grid = select_grid_block(scenario_config, "tri_engine_agreement", args.fast)

    strikes = grid["strikes"]
    spot = float(grid["spot"])
    rate = float(grid["rate"])
    dividend = float(grid["dividend"])
    vol = float(grid["vol"])
    tenor = float(grid["tenor"])
    paths = int(grid["paths"])
    seed = int(grid["seed"])
    steps = int(grid["steps"])
    nodes = int(grid["nodes"])

    df = build_dataset(
        args.quant_cli,
        strikes,
        spot,
        rate,
        dividend,
        vol,
        tenor,
        paths,
        seed,
        steps,
        nodes,
    )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv, index=False, float_format="%.8f")
    plot(df, Path(args.output))

    max_mc_abs_error = float(df["mc_abs_error"].max())
    max_pde_abs_error = float(df["pde_abs_error"].max())

    tol = tolerance_config.get("tri_engine_agreement", {})
    tolerance_checks = {}
    if "max_mc_abs_error" in tol:
        tolerance_checks["max_mc_abs_error_ok"] = (
            max_mc_abs_error <= float(tol["max_mc_abs_error"])
        )
    if "max_pde_abs_error" in tol:
        tolerance_checks["max_pde_abs_error_ok"] = (
            max_pde_abs_error <= float(tol["max_pde_abs_error"])
        )
    if "min_mc_ci_coverage" in tol and "mc_std_error" in df.columns:
        ci_low = df["mc_price"] - 1.96 * df["mc_std_error"]
        ci_high = df["mc_price"] + 1.96 * df["mc_std_error"]
        coverage = ((df["bs_price"] >= ci_low) & (df["bs_price"] <= ci_high)).mean()
        tolerance_checks["mc_ci_coverage_ok"] = (
            float(coverage) >= float(tol["min_mc_ci_coverage"])
        )

    payload = {
        "spot": spot,
        "rate": rate,
        "dividend": dividend,
        "vol": vol,
        "tenor": tenor,
        "paths": paths,
        "seed": seed,
        "steps": steps,
        "nodes": nodes,
        "fast": bool(args.fast),
        "csv": str(args.csv),
        "figure": str(args.output),
        "rows": len(df),
        "max_mc_abs_error": max_mc_abs_error,
        "max_pde_abs_error": max_pde_abs_error,
        "protocol": protocol_entry,
        "tolerances": tol,
        "tolerance_checks": tolerance_checks,
        "inputs": describe_inputs([args.quant_cli, args.scenario_grid, args.tolerances]),
    }
    update_run("tri_engine_agreement", payload)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.csv}")


if __name__ == "__main__":
    main()

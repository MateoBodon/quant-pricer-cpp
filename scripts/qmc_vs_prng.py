#!/usr/bin/env python3
"""
Compare pseudorandom MC vs Sobol QMC for European and Asian GBM options.

Outputs:
  * artifacts/qmc_vs_prng.csv   - RMSE table
  * artifacts/qmc_vs_prng.png   - log-log RMSE figure with slopes
"""
from __future__ import annotations

import argparse
import math
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm, qmc

from manifest_utils import update_run


@dataclass
class MarketSpec:
    spot: float = 100.0
    strike: float = 100.0
    rate: float = 0.02
    dividend: float = 0.00
    vol: float = 0.2
    tenor: float = 1.0


def black_scholes_call(mkt: MarketSpec) -> float:
    S, K, r, q, sigma, T = mkt.spot, mkt.strike, mkt.rate, mkt.dividend, mkt.vol, mkt.tenor
    if T <= 0:
        return max(S - K, 0.0)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return S * math.exp(-q * T) * nd1 - K * math.exp(-r * T) * nd2


def simulate_call_price(mkt: MarketSpec, normals: np.ndarray) -> float:
    z = normals.reshape(-1)
    drift = (mkt.rate - mkt.dividend - 0.5 * mkt.vol**2) * mkt.tenor
    diffusion = mkt.vol * math.sqrt(mkt.tenor) * z
    terminal = mkt.spot * np.exp(drift + diffusion)
    payoff = np.maximum(terminal - mkt.strike, 0.0)
    return math.exp(-mkt.rate * mkt.tenor) * float(np.mean(payoff))


def simulate_asian_price(mkt: MarketSpec, normals: np.ndarray, steps: int) -> float:
    normals = normals.reshape(-1, steps)
    dt = mkt.tenor / steps
    drift = (mkt.rate - mkt.dividend - 0.5 * mkt.vol**2) * dt
    diffusion = mkt.vol * math.sqrt(dt) * normals
    log_paths = np.cumsum(drift + diffusion, axis=1)
    spot_paths = mkt.spot * np.exp(log_paths)
    averages = np.mean(spot_paths, axis=1)
    payoff = np.maximum(averages - mkt.strike, 0.0)
    return math.exp(-mkt.rate * mkt.tenor) * float(np.mean(payoff))


def generate_normals(
    paths: int,
    dims: int,
    method: str,
    seed: int,
) -> np.ndarray:
    if method == "prng":
        rng = np.random.default_rng(seed)
        return rng.standard_normal(size=(paths, dims))
    sobol = qmc.Sobol(d=dims, scramble=True, seed=seed)
    u = sobol.random(paths)
    u = np.clip(u, 1e-12, 1.0 - 1e-12)
    return norm.ppf(u)


def estimator(
    mkt: MarketSpec,
    paths: int,
    method: str,
    seed: int,
    kind: str,
    steps: int,
) -> float:
    dims = 1 if kind == "call" else steps
    normals = generate_normals(paths, dims, method, seed)
    if kind == "call":
        return simulate_call_price(mkt, normals)
    return simulate_asian_price(mkt, normals, steps)


def rmse_over_replicates(
    mkt: MarketSpec,
    paths: int,
    method: str,
    kind: str,
    steps: int,
    reps: int,
    base_seed: int,
) -> Tuple[float, float]:
    estimates = []
    for rep in range(reps):
        seed = base_seed + rep * 991
        estimates.append(
            estimator(
                mkt=mkt,
                paths=paths,
                method=method,
                seed=seed,
                kind=kind,
                steps=steps,
            )
        )
    estimates = np.array(estimates)
    rmse = float(np.std(estimates, ddof=1))
    mean_est = float(np.mean(estimates))
    return rmse, mean_est


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="Use fewer paths for CI")
    ap.add_argument(
        "--output",
        default="artifacts/qmc_vs_prng.png",
        help="Output figure path",
    )
    ap.add_argument(
        "--csv",
        default="artifacts/qmc_vs_prng.csv",
        help="CSV output path for summary table",
    )
    ap.add_argument("--seed", type=int, default=4242)
    args = ap.parse_args()

    mkt_call = MarketSpec()
    mkt_asian = MarketSpec()
    steps_asian = 12

    if args.fast:
        path_grid = [256, 512, 1024, 2048]
        reps = 6
    else:
        path_grid = [512, 1024, 2048, 4096, 8192, 16384]
        reps = 12

    plot_rows: List[Dict[str, float | str]] = []
    results_summary: Dict[str, Dict[str, Dict[str, float]]] = {}

    for kind, mkt, steps in [
        ("call", mkt_call, 1),
        ("asian", mkt_asian, steps_asian),
    ]:
        results_summary[kind] = {}
        for method in ["prng", "qmc"]:
            rmses = []
            means = []
            for idx, paths in enumerate(path_grid):
                rmse, mean_est = rmse_over_replicates(
                    mkt=mkt,
                    paths=paths,
                    method=method,
                    kind=kind,
                    steps=steps,
                    reps=reps,
                    base_seed=args.seed + idx * 199,
                )
                rmses.append(rmse)
                means.append(mean_est)
            log_paths = np.log(path_grid)
            log_rmse = np.log(rmses)
            slope, intercept = np.polyfit(log_paths, log_rmse, 1)
            results_summary[kind][method] = {
                "slope": float(slope),
                "intercept": float(intercept),
                "rmse": rmses,
                "means": means,
            }

    summary_rows: List[Dict[str, float | str]] = []
    for kind in ["call", "asian"]:
        slope_prng = results_summary[kind]["prng"]["slope"]
        slope_qmc = results_summary[kind]["qmc"]["slope"]
        prng_rmse = results_summary[kind]["prng"]["rmse"]
        qmc_rmse = results_summary[kind]["qmc"]["rmse"]
        for idx, paths in enumerate(path_grid):
            summary_rows.append(
                {
                    "payoff": kind,
                    "paths": paths,
                    "rmse_prng": prng_rmse[idx],
                    "rmse_qmc": qmc_rmse[idx],
                    "slope_prng": slope_prng,
                    "slope_qmc": slope_qmc,
                }
            )
            plot_rows.append(
                {
                    "payoff": kind,
                    "method": "prng",
                    "paths": paths,
                    "rmse": prng_rmse[idx],
                }
            )
            plot_rows.append(
                {
                    "payoff": kind,
                    "method": "qmc",
                    "paths": paths,
                    "rmse": qmc_rmse[idx],
                }
            )

    summary_df = pd.DataFrame(summary_rows)
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(csv_path, index=False, float_format="%.8f")

    plot_df = pd.DataFrame(plot_rows)

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, kind, title in zip(
        axes,
        ["call", "asian"],
        ["GBM European Call", "Arithmetic Asian Call"],
    ):
        subset = plot_df[plot_df["payoff"] == kind]
        for method, marker, color in [
            ("prng", "o-", "#1f77b4"),
            ("qmc", "s--", "#ff7f0e"),
        ]:
            data = subset[subset["method"] == method].sort_values("paths")
            ax.loglog(data["paths"], data["rmse"], marker, color=color, label=method.upper())
            slope = results_summary[kind][method]["slope"]
            ax.text(
                0.05 if method == "prng" else 0.55,
                0.1 if method == "prng" else 0.85,
                f"{method.upper()} slope {slope:.2f}",
                transform=ax.transAxes,
                color=color,
                fontsize=8,
            )
        ax.set_title(title)
        ax.set_xlabel("Paths")
        ax.grid(True, which="both", ls=":", alpha=0.5)
    axes[0].set_ylabel("RMSE (std over replicates)")
    axes[1].legend(loc="upper right")
    fig.suptitle("RMSE Scaling: QMC vs PRNG")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    slopes = {
        kind: {
            "prng": results_summary[kind]["prng"]["slope"],
            "qmc": results_summary[kind]["qmc"]["slope"],
        }
        for kind in ["call", "asian"]
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fast": bool(args.fast),
        "seed": args.seed,
        "paths": path_grid,
        "reps": reps,
        "asian_steps": steps_asian,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "slopes": slopes,
        "csv_rows": int(len(summary_df)),
        "inputs": [],
    }
    payload["command"] = shlex.join([sys.executable] + sys.argv)
    update_run("qmc_vs_prng", payload)
    print(f"Wrote {fig_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()

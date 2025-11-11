#!/usr/bin/env python3
"""
Compare pseudorandom MC vs Sobol QMC at equal wall-clock budgets.

Outputs (defaults under docs/artifacts/):
  * qmc_vs_prng_equal_time.csv  – RMSE for matched time budgets
  * qmc_vs_prng_equal_time.png  – log-log curves (RMSE vs seconds)
"""
from __future__ import annotations

import argparse
import math
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import update_run
from scipy.stats import norm, qmc


@dataclass
class MarketSpec:
    spot: float = 100.0
    strike: float = 100.0
    rate: float = 0.02
    dividend: float = 0.00
    vol: float = 0.2
    tenor: float = 1.0


def black_scholes_call(mkt: MarketSpec) -> float:
    S, K, r, q, sigma, T = (
        mkt.spot,
        mkt.strike,
        mkt.rate,
        mkt.dividend,
        mkt.vol,
        mkt.tenor,
    )
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


def generate_normals(paths: int, dims: int, method: str, seed: int) -> np.ndarray:
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
) -> Tuple[float, float, float]:
    estimates: List[float] = []
    tic = perf_counter()
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
    duration = perf_counter() - tic
    estimates_arr = np.array(estimates, dtype=float)
    rmse = float(np.std(estimates_arr, ddof=1))
    mean_est = float(np.mean(estimates_arr))
    return rmse, mean_est, duration


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="Use fewer paths for CI")
    ap.add_argument(
        "--output",
        default="artifacts/qmc_vs_prng_equal_time.png",
        help="Output figure path",
    )
    ap.add_argument(
        "--csv",
        default="artifacts/qmc_vs_prng_equal_time.csv",
        help="CSV output path for summary table",
    )
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument(
        "--budget-count",
        type=int,
        default=6,
        help="Number of equal-time budgets to report (per payoff)",
    )
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

    budget_count = max(3, args.budget_count)

    summary_rows: List[Dict[str, float | str]] = []
    plot_rows: List[Dict[str, float | str]] = []
    payload_stats: Dict[str, Dict[str, Dict[str, float | List[float]]]] = {}

    payoff_specs = [
        ("call", mkt_call, 1, "GBM European Call"),
        ("asian", mkt_asian, steps_asian, "Arithmetic Asian Call"),
    ]

    for kind, mkt, steps, _title in payoff_specs:
        payload_stats[kind] = {}
        method_stats: Dict[str, Dict[str, float | List[float]]] = {}
        for method in ["prng", "qmc"]:
            stats: List[Dict[str, float]] = []
            for idx, paths in enumerate(path_grid):
                rmse, mean_est, duration = rmse_over_replicates(
                    mkt=mkt,
                    paths=paths,
                    method=method,
                    kind=kind,
                    steps=steps,
                    reps=reps,
                    base_seed=args.seed + idx * 199,
                )
                stats.append(
                    {
                        "paths": paths,
                        "rmse": rmse,
                        "mean": mean_est,
                        "duration": duration,
                    }
                )
            log_paths = np.log([s["paths"] for s in stats])
            log_rmse = np.log([s["rmse"] for s in stats])
            slope, intercept = np.polyfit(log_paths, log_rmse, 1)
            time_per_run = np.array([s["duration"] / reps for s in stats], dtype=float)
            time_per_path = time_per_run / np.array(
                [s["paths"] for s in stats], dtype=float
            )
            rmse_constant = float(
                np.mean([s["rmse"] * math.sqrt(s["paths"]) for s in stats])
            )
            avg_time_per_path = float(np.mean(time_per_path))
            stats_dict = {
                "paths": [s["paths"] for s in stats],
                "rmse": [s["rmse"] for s in stats],
                "means": [s["mean"] for s in stats],
                "duration_per_run": time_per_run.tolist(),
                "avg_time_per_path": avg_time_per_path,
                "rmse_constant": rmse_constant,
                "slope": float(slope),
                "intercept": float(intercept),
            }
            method_stats[method] = stats_dict
            payload_stats[kind][method] = stats_dict

        min_budget = min(
            min(method_stats[method]["duration_per_run"])  # type: ignore[arg-type]
            for method in ["prng", "qmc"]
        )
        max_budget = max(
            max(method_stats[method]["duration_per_run"])  # type: ignore[arg-type]
            for method in ["prng", "qmc"]
        )
        time_grid = np.geomspace(min_budget, max_budget, num=budget_count)
        payload_stats[kind]["time_grid"] = list(map(float, time_grid))

        for method in ["prng", "qmc"]:
            avg_time = float(method_stats[method]["avg_time_per_path"])  # type: ignore[assignment]
            rmse_const = float(method_stats[method]["rmse_constant"])  # type: ignore[assignment]
            rmse_vs_time: List[float] = []
            paths_vs_time: List[float] = []
            for budget in time_grid:
                effective_paths = max(1.0, budget / avg_time)
                paths_vs_time.append(effective_paths)
                rmse_vs_time.append(rmse_const / math.sqrt(effective_paths))
                plot_rows.append(
                    {
                        "payoff": kind,
                        "method": method,
                        "time_seconds": budget,
                        "rmse": rmse_vs_time[-1],
                    }
                )
            method_stats[method]["rmse_vs_time"] = rmse_vs_time  # type: ignore[index]
            method_stats[method]["paths_vs_time"] = paths_vs_time  # type: ignore[index]

        for idx, budget in enumerate(time_grid):
            rmse_prng = method_stats["prng"]["rmse_vs_time"][idx]  # type: ignore[index]
            rmse_qmc = method_stats["qmc"]["rmse_vs_time"][idx]  # type: ignore[index]
            summary_rows.append(
                {
                    "payoff": kind,
                    "time_seconds": float(budget),
                    "paths_prng": float(method_stats["prng"]["paths_vs_time"][idx]),  # type: ignore[index]
                    "paths_qmc": float(method_stats["qmc"]["paths_vs_time"][idx]),  # type: ignore[index]
                    "rmse_prng": float(rmse_prng),
                    "rmse_qmc": float(rmse_qmc),
                    "rmse_ratio": float(rmse_prng / rmse_qmc),
                }
            )

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(csv_path, index=False, float_format="%.10f")

    plot_df = pd.DataFrame(plot_rows)

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (kind, _mkt, _steps, title) in zip(axes, payoff_specs):
        subset = plot_df[plot_df["payoff"] == kind]
        for method, marker, color in [
            ("prng", "o-", "#1f77b4"),
            ("qmc", "s--", "#ff7f0e"),
        ]:
            data = subset[subset["method"] == method].sort_values("time_seconds")
            ax.loglog(
                data["time_seconds"],
                data["rmse"],
                marker,
                color=color,
                label=method.upper(),
            )
        gains = summary_df[summary_df["payoff"] == kind]["rmse_ratio"].to_numpy()
        avg_gain = float(np.mean(gains)) if len(gains) else 1.0
        ax.text(
            0.04,
            0.08,
            f"Avg speedup ≈ {avg_gain:.2f}×",
            transform=ax.transAxes,
            fontsize=8,
        )
        ax.set_title(title)
        ax.set_xlabel("Wall-clock seconds")
        ax.grid(True, which="both", ls=":", alpha=0.5)
    axes[0].set_ylabel("RMSE (std over replicates)")
    axes[1].legend(loc="upper right")
    fig.suptitle("Equal-time RMSE: PRNG vs Sobol QMC")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)

    time_per_path_payload: Dict[str, Dict[str, float]] = {}
    slopes_payload: Dict[str, Dict[str, float]] = {}
    rmse_const_payload: Dict[str, Dict[str, float]] = {}
    time_grid_payload: Dict[str, List[float]] = {}
    for kind, methods in payload_stats.items():
        time_grid_payload[kind] = list(methods.get("time_grid", []))  # type: ignore[arg-type]
        time_per_path_payload[kind] = {}
        slopes_payload[kind] = {}
        rmse_const_payload[kind] = {}
        for method_name, stats in methods.items():
            if method_name == "time_grid":
                continue
            time_per_path_payload[kind][method_name] = float(stats["avg_time_per_path"])
            slopes_payload[kind][method_name] = float(stats["slope"])
            rmse_const_payload[kind][method_name] = float(stats["rmse_constant"])

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fast": bool(args.fast),
        "seed": args.seed,
        "paths": path_grid,
        "reps": reps,
        "budget_count": budget_count,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "csv_rows": int(len(summary_df)),
        "time_per_path": time_per_path_payload,
        "slopes": slopes_payload,
        "time_grid": time_grid_payload,
        "rmse_constants": rmse_const_payload,
        "summary_rows": summary_rows,
        "command": shlex.join([sys.executable] + sys.argv),
        "inputs": [],
    }
    update_run("qmc_vs_prng_equal_time", payload)
    print(f"Wrote {fig_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()

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


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call_price(spot: float, strike: float, rate: float, div: float, vol: float, tenor: float) -> float:
    if vol <= 0.0 or tenor <= 0.0:
        return max(0.0, spot * math.exp(-div * tenor) - strike * math.exp(-rate * tenor))
    sqrt_t = math.sqrt(tenor)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * tenor) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t
    df_r = math.exp(-rate * tenor)
    df_q = math.exp(-div * tenor)
    return spot * df_q * _norm_cdf(d1) - strike * df_r * _norm_cdf(d2)


def _bs_vega(spot: float, strike: float, rate: float, div: float, vol: float, tenor: float) -> float:
    if vol <= 0.0 or tenor <= 0.0:
        return 0.0
    sqrt_t = math.sqrt(tenor)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * tenor) / (vol * sqrt_t)
    df_q = math.exp(-div * tenor)
    return spot * df_q * math.sqrt(1.0 / (2.0 * math.pi)) * math.exp(-0.5 * d1 * d1) * sqrt_t


def _implied_vol_call(price: float, spot: float, strike: float, rate: float, div: float, tenor: float) -> float:
    intrinsic = max(0.0, spot * math.exp(-div * tenor) - strike * math.exp(-rate * tenor))
    if price <= intrinsic + 1e-12:
        return 0.0
    low, high = 1e-4, 5.0
    for _ in range(80):
        mid = 0.5 * (low + high)
        val = _bs_call_price(spot, strike, rate, div, mid, tenor)
        if val > price:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


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
    step_grid = [8, 16, 32, 64, 128]
    if args.fast:
        step_grid = [8, 16, 32, 64]

    paths_hi = max(30_000, args.paths)
    paths_lo = max(20_000, args.paths // 3)
    path_grid = [paths_hi] if args.fast else [paths_lo, paths_hi]

    scenarios = [
        {
            "name": "base",
            "kappa": 1.5,
            "theta": 0.04,
            "sigma": 0.5,
            "rho": -0.5,
            "v0": 0.04,
            "tenor": 1.0,
        },
        {
            "name": "high_volvol",
            "kappa": 1.2,
            "theta": 0.04,
            "sigma": 0.9,
            "rho": -0.7,
            "v0": 0.04,
            "tenor": 1.0,
        },
        {
            "name": "near_feller",
            "kappa": 0.35,
            "theta": 0.04,
            "sigma": 0.9,
            "rho": -0.3,
            "v0": 0.01,
            "tenor": 0.5,
        },
    ]

    market = {
        "spot": 100.0,
        "strike": 100.0,
        "rate": 0.01,
        "dividend": 0.0,
    }

    def make_cli_args(scenario: Dict[str, float], step_count: int, path_count: int) -> List[Any]:
        return [
            "heston",
            scenario["kappa"],
            scenario["theta"],
            scenario["sigma"],
            scenario["rho"],
            scenario["v0"],
            market["spot"],
            market["strike"],
            market["rate"],
            market["dividend"],
            scenario["tenor"],
            path_count,
            step_count,
            args.seed,
        ]

    results = []
    commands: List[str] = []
    for scenario in scenarios:
        for path_count in path_grid:
            for scheme_flag, label in (("--heston-qe", "qe"), ("--heston-euler", "euler")):
                for steps in step_grid:
                    cmd = [
                        *make_cli_args(scenario, steps, path_count),
                        "--mc",
                        "--json",
                        scheme_flag,
                        "--rng=counter",
                    ]
                    res = _run_cli_json(cli, cmd)
                    price = float(res.get("price", math.nan))
                    analytic_price = float(res.get("analytic", math.nan))
                    std_error = float(res.get("std_error", math.nan))
                    ci_low = float(res.get("ci_low", price))
                    ci_high = float(res.get("ci_high", price))

                    analytic_iv = _implied_vol_call(
                        analytic_price,
                        market["spot"],
                        market["strike"],
                        market["rate"],
                        market["dividend"],
                        scenario["tenor"],
                    )
                    model_iv = _implied_vol_call(
                        price,
                        market["spot"],
                        market["strike"],
                        market["rate"],
                        market["dividend"],
                        scenario["tenor"],
                    )
                    vega = _bs_vega(
                        market["spot"],
                        market["strike"],
                        market["rate"],
                        market["dividend"],
                        max(analytic_iv, 1e-4),
                        scenario["tenor"],
                    )
                    bias_price = price - analytic_price
                    rmse_price = math.sqrt(bias_price * bias_price + std_error * std_error)
                    bias_iv = model_iv - analytic_iv
                    iv_se = std_error / vega if vega > 1e-12 else 0.0
                    rmse_iv = math.sqrt(bias_iv * bias_iv + iv_se * iv_se)

                    results.append(
                        {
                            "scenario": scenario["name"],
                            "scheme": label,
                            "steps": steps,
                            "paths": path_count,
                            "price": price,
                            "std_error": std_error,
                            "ci_low": ci_low,
                            "ci_high": ci_high,
                            "analytic_price": analytic_price,
                            "model_iv": model_iv,
                            "analytic_iv": analytic_iv,
                            "bias_price": bias_price,
                            "rmse_price": rmse_price,
                            "bias_iv": bias_iv,
                            "rmse_iv": rmse_iv,
                        }
                    )
                    commands.append(shlex.join([str(cli), *[str(arg) for arg in cmd]]))

    df = pd.DataFrame(results).sort_values(["scenario", "scheme", "paths", "steps"])
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.8f")

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0))
    plot_df = df[df["paths"] == df["paths"].max()]
    for label, marker in (("qe", "o"), ("euler", "s")):
        for scenario_name, group in plot_df[plot_df["scheme"] == label].groupby("scenario"):
            axes[0].loglog(
                group["steps"],
                group["rmse_price"],
                marker=marker,
                label=f"{scenario_name}-{label}",
            )
            axes[1].loglog(
                group["steps"],
                group["rmse_iv"],
                marker=marker,
                label=f"{scenario_name}-{label}",
            )
    axes[0].set_xlabel("Time steps")
    axes[0].set_ylabel("Price RMSE (abs)")
    axes[0].set_title(f"Price RMSE vs steps (paths={plot_df['paths'].max():,})")
    axes[0].grid(True, which="both", linestyle=":", alpha=0.5)

    axes[1].set_xlabel("Time steps")
    axes[1].set_ylabel("Implied vol RMSE")
    axes[1].set_title("IV RMSE vs steps (same paths)")
    axes[1].grid(True, which="both", linestyle=":", alpha=0.5)

    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    fig.suptitle(f"Heston QE vs analytic (seed={args.seed})")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    payload = {
        "paths_grid": path_grid,
        "seed": args.seed,
        "step_grid": step_grid,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "commands": commands,
        "results": results,
        "scenarios": scenarios,
    }
    update_run("heston_qe_vs_analytic", payload)

    print(f"Wrote {csv_path}")
    print(f"Wrote {fig_path}")


if __name__ == "__main__":
    main()

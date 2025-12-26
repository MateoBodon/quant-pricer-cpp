#!/usr/bin/env python3
"""
Micro-figure for put–call parity residuals and digital approximations.

Generates a CSV/PNG showing parity tightness and the alignment between
Black–Scholes digital prices and a strike finite-difference of the call.
"""
from __future__ import annotations

import argparse
import math
import shlex
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run


def black_scholes_call(
    S: float, K: float, r: float, q: float, sigma: float, T: float
) -> float:
    if T <= 0:
        return max(S - K, 0.0)
    sigma = max(sigma, 1e-9)
    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    Nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    Nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return S * math.exp(-q * T) * Nd1 - K * math.exp(-r * T) * Nd2


def black_scholes_put(
    S: float, K: float, r: float, q: float, sigma: float, T: float
) -> float:
    call = black_scholes_call(S, K, r, q, sigma, T)
    return call - S * math.exp(-q * T) + K * math.exp(-r * T)


def black_scholes_digital_call(
    S: float, K: float, r: float, q: float, sigma: float, T: float
) -> float:
    if T <= 0:
        return 1.0 if S > K else 0.0
    sigma = max(sigma, 1e-9)
    sqrtT = math.sqrt(T)
    d2 = (math.log(S / K) + (r - q - 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    Nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return math.exp(-r * T) * Nd2


def build_grid(fast: bool) -> pd.DataFrame:
    spot = 100.0
    rates = 0.02
    div = 0.01
    sigma = 0.22
    strikes = np.linspace(90.0, 110.0, 5 if fast else 9)
    tenors = (
        np.array([0.25, 0.5, 1.0]) if fast else np.array([0.25, 0.5, 0.75, 1.0, 1.5])
    )
    rows = []
    eps = 0.25
    for T in tenors:
        for K in strikes:
            call = black_scholes_call(spot, K, rates, div, sigma, T)
            put = black_scholes_put(spot, K, rates, div, sigma, T)
            parity_residual = (
                call - put - (spot * math.exp(-div * T) - K * math.exp(-rates * T))
            )
            delta = (
                black_scholes_call(spot + 1e-4, K, rates, div, sigma, T) - call
            ) / 1e-4
            digital_analytic = black_scholes_digital_call(spot, K, rates, div, sigma, T)
            call_up = black_scholes_call(spot, K + eps, rates, div, sigma, T)
            call_dn = black_scholes_call(spot, K - eps, rates, div, sigma, T)
            digital_fd = -(call_up - call_dn) / (2.0 * eps)
            rows.append(
                {
                    "spot": spot,
                    "strike": float(K),
                    "tenor": float(T),
                    "rate": rates,
                    "dividend": div,
                    "vol": sigma,
                    "call_price": call,
                    "put_price": put,
                    "parity_residual": parity_residual,
                    "delta": delta,
                    "digital_analytic": digital_analytic,
                    "digital_fd": digital_fd,
                    "digital_diff": digital_fd - digital_analytic,
                }
            )
    return pd.DataFrame(rows)


def plot_results(df: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for tenor, frame in df.groupby("tenor"):
        axes[0].plot(
            frame["strike"],
            frame["parity_residual"],
            marker="o",
            label=f"T={tenor:.2f}y",
        )
        axes[1].plot(
            frame["strike"], frame["digital_diff"], marker="s", label=f"T={tenor:.2f}y"
        )
    axes[0].axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    axes[0].set_title("Put–Call Parity Residual")
    axes[0].set_xlabel("Strike")
    axes[0].set_ylabel("Residual (price units)")
    axes[1].axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    axes[1].set_title("Digital Call: Finite Difference vs Analytic")
    axes[1].set_xlabel("Strike")
    axes[1].set_ylabel("digital_fd - digital_analytic")
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="Smaller grid for FAST tests")
    ap.add_argument(
        "--output-csv", default=str(ARTIFACTS_ROOT / "parity_checks.csv")
    )
    ap.add_argument(
        "--output-png", default=str(ARTIFACTS_ROOT / "parity_checks.png")
    )
    ap.add_argument("--skip-manifest", action="store_true")
    args = ap.parse_args()

    df = build_grid(args.fast)
    csv_path = Path(args.output_csv)
    png_path = Path(args.output_png)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.8f")
    plot_results(df, png_path)

    if not args.skip_manifest:
        command = shlex.join([sys.executable] + sys.argv)
        manifest_entry = {
            "command": command,
            "fast": bool(args.fast),
            "csv": str(csv_path),
            "png": str(png_path),
            "rows": int(len(df)),
            "inputs": describe_inputs([]),
        }
        update_run("parity_checks", manifest_entry, append=True, id_field=None)

    print(f"Parity checks CSV -> {csv_path}")
    print(f"Parity checks figure -> {png_path}")


if __name__ == "__main__":
    main()

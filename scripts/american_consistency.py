#!/usr/bin/env python3
"""
Cross-check American put pricing consistency across PSOR, CRR, and LSMC solvers.

Outputs:
  * artifacts/american_consistency.csv
  * artifacts/american_consistency.png
"""
from __future__ import annotations

import argparse
import math
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from manifest_utils import update_run


@dataclass
class AmericanSpec:
    spot: float
    strike: float
    rate: float = 0.02
    dividend: float = 0.00
    vol: float = 0.2
    tenor: float = 1.0


def american_put_psor(
    spec: AmericanSpec,
    m_nodes: int,
    n_steps: int,
    smax_mult: float = 4.0,
    omega: float = 1.5,
    tol: float = 1e-8,
    max_iter: int = 10_000,
) -> float:
    K = spec.strike
    S_max = smax_mult * K
    dS = S_max / m_nodes
    dt = spec.tenor / n_steps
    grid_S = np.linspace(0, S_max, m_nodes + 1)
    intrinsic = np.maximum(K - grid_S, 0.0)
    V = intrinsic.copy()

    j = np.arange(1, m_nodes)
    sigma2 = spec.vol * spec.vol
    r = spec.rate
    q = spec.dividend
    alpha = 0.25 * dt * (sigma2 * j**2 - (r - q) * j)
    beta = -0.5 * dt * (sigma2 * j**2 + r)
    gamma = 0.25 * dt * (sigma2 * j**2 + (r - q) * j)

    a = -alpha
    b = 1.0 - beta
    c = -gamma
    d = alpha
    e = 1.0 + beta
    f = gamma

    for _ in range(n_steps):
        rhs = d * V[:-2] + e * V[1:-1] + f * V[2:]
        x = V[1:-1].copy()
        for _ in range(max_iter):
            x_old = x.copy()
            max_diff = 0.0
            for idx in range(len(x)):
                lower = V[0] if idx == 0 else x[idx - 1]
                upper = V[-1] if idx == len(x) - 1 else x_old[idx + 1]
                numer = rhs[idx] - a[idx] * lower - c[idx] * upper
                new_val = (1.0 - omega) * x[idx] + omega * (numer / b[idx])
                new_val = max(intrinsic[idx + 1], new_val)
                max_diff = max(max_diff, abs(new_val - x[idx]))
                x[idx] = new_val
            if max_diff < tol:
                break
        V[1:-1] = x
        V[0] = K
        V[-1] = 0.0

    S0_idx = int(spec.spot / dS)
    S0 = spec.spot
    if S0_idx >= m_nodes:
        return 0.0
    # Linear interpolation around the nearest grid points
    S_lower = grid_S[S0_idx]
    S_upper = grid_S[S0_idx + 1]
    V_lower = V[S0_idx]
    V_upper = V[S0_idx + 1]
    if S_upper == S_lower:
        return float(V_lower)
    return float(V_lower + (V_upper - V_lower) * (S0 - S_lower) / (S_upper - S_lower))


def american_put_binomial(spec: AmericanSpec, steps: int) -> float:
    T = spec.tenor
    dt = T / steps
    u = math.exp(spec.vol * math.sqrt(dt))
    d = 1.0 / u
    disc = math.exp(-spec.rate * dt)
    p = (math.exp((spec.rate - spec.dividend) * dt) - d) / (u - d)
    S = np.array([spec.spot * (u ** (steps - k)) * (d**k) for k in range(steps + 1)])
    option = np.maximum(spec.strike - S, 0.0)
    for step in range(steps, 0, -1):
        S = S[:-1] * d
        option = disc * (p * option[:-1] + (1.0 - p) * option[1:])
        intrinsic = np.maximum(spec.strike - S, 0.0)
        option = np.maximum(option, intrinsic)
    return float(option[0])


def american_put_lsmc(
    spec: AmericanSpec,
    paths: int,
    steps: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dt = spec.tenor / steps
    discount = math.exp(-spec.rate * dt)
    z = rng.standard_normal(size=(paths, steps))
    drift = (spec.rate - spec.dividend - 0.5 * spec.vol**2) * dt
    diffusion = spec.vol * math.sqrt(dt) * z
    log_paths = np.cumsum(drift + diffusion, axis=1)
    S = spec.spot * np.exp(log_paths)
    S = np.column_stack([np.full(paths, spec.spot), S])

    cashflows = np.maximum(spec.strike - S[:, -1], 0.0)
    for t in range(steps - 1, 0, -1):
        payoff = np.maximum(spec.strike - S[:, t], 0.0)
        cashflows *= discount
        itm = payoff > 0
        if not np.any(itm):
            continue
        X = S[itm, t]
        Y = cashflows[itm]
        A = np.column_stack([np.ones_like(X), X, X**2])
        coeffs, *_ = np.linalg.lstsq(A, Y, rcond=None)
        continuation = A @ coeffs
        exercise = payoff[itm]
        exercise_mask = exercise > continuation
        cashflows[itm] = np.where(exercise_mask, exercise, Y)
    cashflows *= discount
    intrinsic0 = max(spec.strike - spec.spot, 0.0)
    price = max(intrinsic0, float(np.mean(cashflows)))
    se = float(np.std(cashflows, ddof=1) / math.sqrt(paths))
    return price, se


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="FAST mode for CI")
    ap.add_argument("--seed", type=int, default=2025)
    ap.add_argument("--output", default="artifacts/american_consistency.png")
    ap.add_argument("--csv", default="artifacts/american_consistency.csv")
    args = ap.parse_args()

    strike = 100.0
    ratios = [0.8, 1.0, 1.2]
    sigmas = [0.2, 0.4]
    r = 0.02
    q = 0.01
    T = 1.0

    if args.fast:
        psor_nodes = 160
        psor_steps = 160
        binomial_steps = 128
        lsmc_paths = 2000
        lsmc_steps = 32
    else:
        psor_nodes = 220
        psor_steps = 220
        binomial_steps = 256
        lsmc_paths = 6000
        lsmc_steps = 64

    rows: List[Dict] = []
    for sigma in sigmas:
        for ratio in ratios:
            spot = strike * ratio
            spec = AmericanSpec(
                spot=spot,
                strike=strike,
                rate=r,
                dividend=q,
                vol=sigma,
                tenor=T,
            )
            psor_price = american_put_psor(spec, psor_nodes, psor_steps)
            crr_price = american_put_binomial(spec, binomial_steps)
            lsmc_price, lsmc_se = american_put_lsmc(spec, lsmc_paths, lsmc_steps, args.seed)
            rows.append(
                {
                    "spot": spot,
                    "strike": strike,
                    "ratio": ratio,
                    "sigma": sigma,
                    "psor": psor_price,
                    "crr": crr_price,
                    "lsmc": lsmc_price,
                    "lsmc_se": lsmc_se,
                    "lsmc_lo": lsmc_price - 2.0 * lsmc_se,
                    "lsmc_hi": lsmc_price + 2.0 * lsmc_se,
                    "psor_nodes": psor_nodes,
                    "psor_steps": psor_steps,
                    "binomial_steps": binomial_steps,
                    "lsmc_paths": lsmc_paths,
                    "lsmc_steps": lsmc_steps,
                }
            )

    df = pd.DataFrame(rows)
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(sigmas), figsize=(10, 4), sharey=True)
    for ax, sigma in zip(axes, sigmas):
        subset = df[df["sigma"] == sigma].sort_values("ratio")
        ax.plot(subset["ratio"], subset["psor"], "o-", label="PSOR", color="#1f77b4")
        ax.plot(subset["ratio"], subset["crr"], "s--", label="CRR", color="#2ca02c")
        ax.errorbar(
            subset["ratio"],
            subset["lsmc"],
            yerr=2.0 * subset["lsmc_se"],
            fmt="^",
            label="LSMC ±2σ",
            color="#ff7f0e",
            capsize=4,
        )
        ax.set_title(f"σ = {sigma:.2f}")
        ax.set_xlabel("Spot / Strike")
        ax.grid(True, alpha=0.4)
    axes[0].set_ylabel("American Put Price")
    axes[-1].legend(loc="upper left")
    fig.suptitle("American Put Consistency: PSOR vs CRR vs LSMC")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fast": bool(args.fast),
        "seed": args.seed,
        "psor_nodes": psor_nodes,
        "psor_steps": psor_steps,
        "binomial_steps": binomial_steps,
        "lsmc_paths": lsmc_paths,
        "lsmc_steps": lsmc_steps,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "grid": rows,
    }
    payload["command"] = shlex.join([sys.executable] + sys.argv)
    update_run("american_consistency", payload)
    print(f"Wrote {fig_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Minimal Python walkthrough for pyquant_pricer bindings.

Run with:
  python -m python.examples.quickstart
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyquant_pricer as qp


def price_vanilla() -> None:
    spot = 100.0
    strike = 105.0
    rate = 0.02
    dividend = 0.01
    vol = 0.25
    expiry = 0.5
    call = qp.bs_call(spot, strike, rate, dividend, vol, expiry)
    delta = qp.bs_delta_call(spot, strike, rate, dividend, vol, expiry)
    print(f"Black–Scholes call: {call:.4f} (delta {delta:.4f})")


def price_barrier() -> None:
    barrier = qp.BarrierSpec()
    barrier.type = qp.BarrierType.DownOut
    barrier.B = 95.0
    barrier.rebate = 0.0
    spot = 100.0
    strike = 100.0
    rate = 0.03
    dividend = 0.0
    vol = 0.2
    expiry = 1.0
    price = qp.barrier_bs(
        qp.OptionType.Call, barrier, spot, strike, rate, dividend, vol, expiry
    )
    print(f"Down-and-out call (analytic RR): {price:.4f}")


def heston_helpers() -> None:
    params = qp.HestonParams()
    params.kappa = 1.5
    params.theta = 0.04
    params.sigma = 0.5
    params.rho = -0.5
    params.v0 = 0.04

    market = qp.HestonMarket()
    market.spot = 100.0
    market.strike = 100.0
    market.rate = 0.01
    market.dividend = 0.0
    market.time = 1.0

    iv = qp.heston_implied_vol(market, params)
    phi = qp.heston_characteristic_fn(1.0, market, params)
    print(
        f"Heston analytic call IV: {iv:.4%} | phi(1) = {phi.real:.4f} + {phi.imag:.4f}i"
    )


def price_heston_batch() -> None:
    """Price an analytic Heston batch; no simulation or market data is used."""
    markets = np.array(
        [
            [100.0, 90.0, 0.015, 0.005, 0.5],
            [100.0, 100.0, 0.015, 0.005, 1.0],
            [100.0, 110.0, 0.015, 0.005, 2.0],
        ],
        dtype=np.float64,
    )
    params = np.array([[1.5, 0.04, 0.6, -0.45, 0.04]])
    metrics = qp.heston_call_metrics_batch(markets, params)
    print(f"Heston analytic batch: [call_price, implied_vol] {metrics.tolist()}")


def portfolio_risk_and_stress() -> None:
    """Value and stress a mixed long/short call-put portfolio."""
    positions = np.array(
        [
            [1, 120, 100, 95, 0.03, 0.01, 0.22, 90 / 365],
            [-1, -80, 100, 105, 0.03, 0.01, 0.25, 90 / 365],
            [1, 50, 100, 110, 0.03, 0.01, 0.28, 180 / 365],
        ],
        dtype=np.float64,
    )
    risk = qp.bs_portfolio_risk(positions)
    totals = dict(zip(risk["total_columns"], risk["portfolio_totals"]))
    shocks = np.array(
        [[0, 0, 0, 0, 0], [-0.10, 0.08, 0.01, 0, 1 / 365]],
        dtype=np.float64,
    )
    pnl = qp.bs_portfolio_scenarios(positions, shocks, detail=False)["portfolio_pnl"]
    print(f"Portfolio risk: {totals}")
    print(f"Exact scenario P&L: {pnl.tolist()}")


def maybe_run_heston(repo_root: Path) -> None:
    optional_modules = ("matplotlib", "pandas", "scipy")
    missing = [
        name for name in optional_modules if importlib.util.find_spec(name) is None
    ]
    if missing:
        print(
            "Optional Heston calibration dependencies are unavailable "
            f"({', '.join(missing)}); skipping calibration demo."
        )
        return
    samples_dir = repo_root / "data" / "samples"
    normalized_dir = repo_root / "data" / "normalized"
    candidates = list(samples_dir.glob("spx_*.csv")) + list(
        normalized_dir.glob("spy_*.csv")
    )
    if not candidates:
        print("No normalized surfaces found; skipping Heston demo.")
        return
    surface = sorted(candidates)[0]
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "calibrate_heston.py"),
        "--input",
        str(surface),
        "--fast",
        "--metric",
        "price",
        "--seed",
        "19",
        "--retries",
        "3",
    ]
    print(f"Running Heston FAST calibration on {surface.name} ...")
    subprocess.run(cmd, cwd=repo_root, check=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    price_vanilla()
    price_barrier()
    heston_helpers()
    price_heston_batch()
    portfolio_risk_and_stress()
    maybe_run_heston(repo_root)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Minimal Python walkthrough for pyquant_pricer bindings.

Run with:
  python -m python.examples.quickstart
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    price = qp.barrier_bs(qp.OptionType.Call, barrier, spot, strike, rate, dividend, vol, expiry)
    print(f"Down-and-out call (analytic RR): {price:.4f}")


def maybe_run_heston(repo_root: Path) -> None:
    samples_dir = repo_root / "data" / "samples"
    normalized_dir = repo_root / "data" / "normalized"
    candidates = list(samples_dir.glob("spx_*.csv")) + list(normalized_dir.glob("spy_*.csv"))
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
    maybe_run_heston(repo_root)


if __name__ == "__main__":
    main()

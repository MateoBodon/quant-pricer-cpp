#!/usr/bin/env python3
"""
Calibrate SABR parameters for a single maturity slice using Hagan's formula.

Input CSV: call_put, strike, mid, rate, q, spot, maturity_years

Usage:
  python scripts/sabr_slice_calibration.py --csv data/options.csv --target_T 0.5 --out artifacts/sabr_slice_T0.5.json
"""
import argparse
import json
import math
import os

import numpy as np
import pandas as pd


def bs_price_call(S, K, r, q, sigma, T):
    if T <= 0 or sigma <= 0:
        return max(0.0, S * math.exp(-q * T) - K * math.exp(-r * T))
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    from math import erf, exp, sqrt

    N1 = 0.5 * (1 + erf(d1 / sqrt(2)))
    N2 = 0.5 * (1 + erf(d2 / sqrt(2)))
    return S * math.exp(-q * T) * N1 - K * math.exp(-r * T) * N2


def implied_vol_from_price(S, K, r, q, T, price):
    # Bisection
    lo, hi = 1e-6, 5.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        val = bs_price_call(S, K, r, q, mid, T)
        if val > price:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def hagan_black_vol(F, K, T, alpha, beta, rho, nu):
    if F == K:
        term1 = (((1 - beta) ** 2) / 24.0) * (alpha * alpha) / (F ** (2 - 2 * beta))
        term2 = 0.25 * rho * beta * nu * alpha / (F ** (1 - beta))
        term3 = ((2 - 3 * rho * rho) / 24.0) * (nu * nu)
        return alpha / (F ** (1 - beta)) * (1 + (term1 + term2 + term3) * T)
    z = (nu / alpha) * ((F * K) ** ((1 - beta) / 2.0)) * math.log(F / K)
    xz = math.log((math.sqrt(1 - 2 * rho * z + z * z) + z - rho) / (1 - rho))
    one_minus_beta = 1 - beta
    A = alpha / ((F * K) ** (one_minus_beta / 2.0))
    B1 = (
        1
        + ((one_minus_beta**2) / 24.0) * ((math.log(F / K)) ** 2)
        + ((one_minus_beta**4) / 1920.0) * ((math.log(F / K)) ** 4)
    )
    vol = A * (z / xz) * B1
    C1 = ((one_minus_beta**2) / 24.0) * (alpha * alpha) / ((F * K) ** (one_minus_beta))
    C2 = 0.25 * rho * beta * nu * alpha / ((F * K) ** ((1 - beta) / 2.0))
    C3 = ((2 - 3 * rho * rho) / 24.0) * (nu * nu)
    return vol * (1 + (C1 + C2 + C3) * T)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--target_T", type=float, required=True)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    # select nearest maturity
    T = args.target_T
    df["dt"] = (df["maturity_years"] - T).abs()
    df = df.sort_values("dt").head(2000)  # take close rows

    # Compute IVs per row
    iv = []
    for _, row in df.iterrows():
        S = row["spot"]
        K = row["strike"]
        r = row["rate"]
        q = row["q"]
        mid = row["mid"]
        if row["call_put"] == "put":
            # parity to call
            df_r = math.exp(-r * T)
            df_q = math.exp(-q * T)
            mid = mid + S * df_q - K * df_r
        iv.append(implied_vol_from_price(S, K, r, q, T, mid))
    df["iv"] = iv

    # SABR fit via simple grid search/least squares
    F = float(df["spot"].iloc[0] * math.exp((df["rate"].iloc[0] - df["q"].iloc[0]) * T))
    K_arr = df["strike"].to_numpy()
    iv_arr = df["iv"].to_numpy()
    beta = args.beta

    # coarse grid search
    best = None
    for alpha in np.linspace(0.01, 0.6, 20):
        for rho in np.linspace(-0.9, 0.9, 19):
            for nu in np.linspace(0.1, 2.0, 20):
                pred = np.array(
                    [hagan_black_vol(F, K, T, alpha, beta, rho, nu) for K in K_arr]
                )
                if not np.all(np.isfinite(pred)):
                    continue
                err = np.nanmean((pred - iv_arr) ** 2)
                if best is None or err < best[0]:
                    best = (err, alpha, rho, nu)
    err, alpha, rho, nu = best

    params = {
        "alpha": float(alpha),
        "beta": float(beta),
        "rho": float(rho),
        "nu": float(nu),
        "T": float(T),
        "F": float(F),
        "mse": float(err),
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(params, fh, indent=2)
        fh.write("\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()

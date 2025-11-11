#!/usr/bin/env python3
"""
Backtest VaR exceptions with Kupiec test from a returns CSV.

Inputs: CSV with columns date, ret (decimal), close

Usage:
  python scripts/risk_backtest.py --csv data/spy_returns.csv --alpha 0.99 --horizon 1 --out artifacts/var_backtest_99.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd


def kupiec_pvalue(num_obs: int, num_exceed: int, alpha: float) -> float:
    # Likelihood ratio test for unconditional coverage
    if num_obs <= 0:
        return 1.0
    p = 1.0 - alpha
    pi = num_exceed / num_obs
    if pi <= 0.0 or pi >= 1.0:
        return 0.0
    lr = -2.0 * (
        (num_obs - num_exceed) * math.log((1 - p) / (1 - pi))
        + num_exceed * math.log(p / pi)
    )
    # p-value from chi-square with 1 df
    from math import erf, sqrt

    # approximate via normal tail of sqrt(lr)
    z = math.sqrt(max(lr, 0.0))
    return 1.0 - 0.5 * (1 + erf(z / math.sqrt(2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--alpha", type=float, default=0.99)
    ap.add_argument("--horizon", type=int, default=1, help="days")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df = df.dropna(subset=["ret"])
    # rolling VaR using normal approximation (placeholder); plug in quant.risk via CLI if preferred
    window = 250
    rets = df["ret"].to_numpy()
    rolling_var = []
    exceptions = []
    alpha = args.alpha
    from math import sqrt

    for i in range(len(rets)):
        if i < window:
            rolling_var.append(np.nan)
            exceptions.append(np.nan)
            continue
        mu = np.mean(rets[i - window : i])
        sd = np.std(rets[i - window : i])
        # one-day VaR using z at alpha
        z = 2.3263478740408408  # ~N^-1(0.99)
        var = -(mu - z * sd)
        rolling_var.append(var)
        exceptions.append(1.0 if rets[i] < -var else 0.0)

    df["var"] = rolling_var
    df["exc"] = exceptions
    n = int(df["exc"].dropna().shape[0])
    x = int(df["exc"].dropna().sum())
    pval = kupiec_pvalue(n, x, alpha)

    result = {
        "alpha": alpha,
        "obs": n,
        "exceptions": x,
        "kupiec_pvalue": pval,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()

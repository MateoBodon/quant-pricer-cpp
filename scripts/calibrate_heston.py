#!/usr/bin/env python3
"""
Calibrate Heston to an options CSV (from WRDS or local), output parameters and figures.

CSV must contain: call_put, strike, mid, rate, q, spot, maturity_years.

Usage:
  python scripts/calibrate_heston.py --csv data/options_2023-06-01.csv --out artifacts/heston_calib_20230601.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares


def heston_call_price(spot, strike, r, q, T, kappa, theta, sigma, rho, v0):
    # Minimal wrapper calling the CLI analytic for consistency
    import subprocess
    cmd = [
        os.path.join('build', 'quant_cli'), 'heston',
        str(kappa), str(theta), str(sigma), str(rho), str(v0),
        str(spot), str(strike), str(r), str(q), str(T),
        '0', '1', '0', '--analytic'
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        return float(out)
    except Exception:
        return np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df = df[(df['maturity_years'] > 1/365.0) & (df['mid'] > 0)]

    S = float(df['spot'].iloc[0])

    # Objective: weighted errors (1 / mid) for relative fit
    def residuals(x):
        kappa, theta, sigma, rho, v0 = x
        res = []
        for _, row in df.iterrows():
            K = row['strike']
            r = row['rate']
            q = row['q']
            T = row['maturity_years']
            model = heston_call_price(S, K, r, q, T, kappa, theta, sigma, rho, v0)
            if row['call_put'] == 'put' and not np.isnan(model):
                # put-call parity
                df_r = math.exp(-r * T)
                df_q = math.exp(-q * T)
                model = model - S * df_q + K * df_r
            w = 1.0 / max(row['mid'], 1e-8)
            res.append(w * (model - row['mid']))
        return np.array(res)

    x0 = np.array([1.5, 0.04, 0.5, -0.5, 0.04])
    lb = np.array([1e-4, 1e-6, 1e-6, -0.999, 1e-6])
    ub = np.array([10.0, 2.00, 5.0, 0.999, 2.0])
    sol = least_squares(residuals, x0, bounds=(lb, ub), max_nfev=100)

    params = {
        'kappa': float(sol.x[0]),
        'theta': float(sol.x[1]),
        'sigma': float(sol.x[2]),
        'rho': float(sol.x[3]),
        'v0': float(sol.x[4]),
        'cost': float(np.sum(sol.fun**2)),
        'num_obs': int(len(df)),
        'csv': args.csv,
    }
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w') as fh:
        json.dump(params, fh, indent=2)
        fh.write('\n')
    print('wrote', args.out)

if __name__ == '__main__':
    main()



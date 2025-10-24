#!/usr/bin/env python3
"""
Generate synthetic options grid and returns series for offline report builds.

Outputs:
  - data/options_synth.csv
  - data/spy_returns.csv
"""
import math
import os
import random


def bs_call(S, K, r, q, sigma, T):
    if T <= 0.0:
        return max(0.0, S - K)
    if sigma <= 0.0:
        fwd = S * math.exp((r - q) * T)
        return math.exp(-r * T) * max(0.0, fwd - K)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    N2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return S * math.exp(-q * T) * N1 - K * math.exp(-r * T) * N2


def make_options_csv(path: str):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    S = 100.0
    r = 0.01
    q = 0.00
    strikes = [S * m for m in [0.7 + 0.02 * i for i in range(31)]]
    tenors = [0.1 + 0.05 * i for i in range(1, 31)]  # 0.15..1.6y
    with open(path, 'w') as fh:
        fh.write('call_put,strike,mid,rate,q,spot,maturity_years\n')
        for T in tenors:
            for K in strikes:
                m = K / S
                # simple smile/skew surface
                sigma = 0.18 + 0.10 * (m - 1.0) ** 2 + 0.03 * (T - 0.5)
                price_c = bs_call(S, K, r, q, sigma, T)
                price_p = price_c - S * math.exp(-q * T) + K * math.exp(-r * T)
                fh.write(f"call,{K:.6f},{price_c:.8f},{r:.6f},{q:.6f},{S:.6f},{T:.6f}\n")
                fh.write(f"put,{K:.6f},{price_p:.8f},{r:.6f},{q:.6f},{S:.6f},{T:.6f}\n")
    print('wrote', path)


def make_returns_csv(path: str, days: int = 1500):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    # GBM-ish synthetic daily returns
    mu = 0.08
    sigma = 0.20
    dt = 1.0 / 252.0
    ret = []
    price = 400.0
    rows = []
    for t in range(days):
        z = random.gauss(0.0, 1.0)
        r = mu * dt + sigma * math.sqrt(dt) * z
        price *= (1.0 + r)
        rows.append((t, r, price))
    with open(path, 'w') as fh:
        fh.write('date,ret,close\n')
        for t, r, p in rows:
            fh.write(f"{t},{r:.8f},{p:.4f}\n")
    print('wrote', path)


def main():
    make_options_csv('data/options_synth.csv')
    make_returns_csv('data/spy_returns.csv')


if __name__ == '__main__':
    main()



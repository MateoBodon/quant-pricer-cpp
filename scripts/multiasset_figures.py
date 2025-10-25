#!/usr/bin/env python3
import argparse
import json
import math
import os
import subprocess

def ensure_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa
    except Exception:
        subprocess.check_call(['python3','-m','pip','install','--quiet','matplotlib'])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--artifacts', default='artifacts')
    args = ap.parse_args()
    os.makedirs(args.artifacts, exist_ok=True)
    ensure_matplotlib()
    try:
        import matplotlib.pyplot as plt
        import pyquant_pricer as qp
    except Exception as e:
        print('error: require pyquant_pricer and matplotlib:', e)
        return

    # Basket vs vanilla: 2-asset basket, vary correlation
    bparams = qp.BasketMcParams()
    bparams.spots = [100.0, 100.0]
    bparams.vols = [0.2, 0.25]
    bparams.dividends = [0.00, 0.00]
    bparams.weights = [0.5, 0.5]
    bparams.rate = 0.02
    bparams.strike = 100.0
    bparams.time = 1.0
    bparams.num_paths = 300000
    bparams.seed = 424242
    xs = [x/10.0 for x in range(-9, 10, 3)]  # -0.9 .. 0.9 step 0.3
    basket_prices = []
    for rho in xs:
        bparams.corr = [1.0, rho, rho, 1.0]
        stat = qp.basket_call_mc(bparams)
        basket_prices.append(stat.value)
    plt.figure(figsize=(6,4))
    plt.plot(xs, basket_prices, marker='o')
    plt.xlabel('Correlation')
    plt.ylabel('Basket call price')
    plt.title('Basket price vs correlation (2 assets)')
    plt.grid(True, linestyle='--', alpha=0.4)
    out1 = os.path.join(args.artifacts, 'basket_correlation.png')
    plt.tight_layout(); plt.savefig(out1, dpi=200); plt.close()

    # Merton jumps: vary lambda
    mparams = qp.MertonParams()
    mparams.spot = 100.0; mparams.strike = 100.0; mparams.rate = 0.02; mparams.dividend = 0.00
    mparams.vol = 0.2; mparams.time = 1.0
    mparams.muJ = -0.05; mparams.sigmaJ = 0.20
    mparams.num_paths = 400000; mparams.seed = 2025
    lambdas = [0.0, 0.25, 0.5, 0.75, 1.0]
    prices = []
    for lam in lambdas:
        mparams.lambda_ = lam
        stat = qp.merton_call_mc(mparams)
        prices.append(stat.value)
    plt.figure(figsize=(6,4))
    plt.plot(lambdas, prices, marker='o')
    plt.xlabel('Jump intensity λ')
    plt.ylabel('Call price')
    plt.title('Merton jump-diffusion: price vs λ')
    plt.grid(True, linestyle='--', alpha=0.4)
    out2 = os.path.join(args.artifacts, 'merton_lambda.png')
    plt.tight_layout(); plt.savefig(out2, dpi=200); plt.close()

if __name__ == '__main__':
    main()



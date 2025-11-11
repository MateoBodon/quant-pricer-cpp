#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import subprocess


def run_cli(cli, args):
    return subprocess.check_output([cli, *map(str, args)], text=True).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default="build/quant_cli")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--seed", type=int, default=424242)
    args = ap.parse_args()

    os.makedirs(args.artifacts, exist_ok=True)

    # Base ATM scenario
    S, K, r, q, sig, T = 100, 100, 0.03, 0.01, 0.2, 1.0
    grid = [100000, 200000, 400000, 800000]

    try:
        import pyquant_pricer as qp
    except Exception as e:
        print("error: pyquant_pricer not available:", e)
        return

    rows = []
    for paths in grid:
        mp = qp.McParams()
        mp.spot = S
        mp.strike = K
        mp.rate = r
        mp.dividend = q
        mp.vol = sig
        mp.time = T
        mp.num_paths = paths
        mp.seed = args.seed
        mp.antithetic = True
        mp.control_variate = False
        g = qp.mc_greeks_call(mp)
        rows.append(
            {
                "paths": paths,
                "gamma_lrm_se": g.gamma_lrm.std_error,
                "gamma_mixed_se": g.gamma_mixed.std_error,
            }
        )

    csv_path = os.path.join(args.artifacts, "greeks_variance.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["paths", "gamma_lrm_se", "gamma_mixed_se"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Plot
    try:
        import matplotlib.pyplot as plt

        has_mpl = True
    except Exception:
        has_mpl = False
    if has_mpl:
        xs = [row["paths"] for row in rows]
        lrm = [row["gamma_lrm_se"] for row in rows]
        mix = [row["gamma_mixed_se"] for row in rows]
        plt.figure(figsize=(6, 4))
        plt.loglog(xs, lrm, marker="o", label="Gamma LRM SE")
        plt.loglog(xs, mix, marker="o", label="Gamma Mixed SE")
        plt.xlabel("Paths")
        plt.ylabel("Std Error")
        plt.title("Gamma estimator variance vs paths")
        plt.grid(True, which="both", linestyle="--", alpha=0.4)
        plt.legend()
        out_png = os.path.join(args.artifacts, "greeks_variance.png")
        plt.tight_layout()
        plt.savefig(out_png, dpi=200)
        plt.close()


if __name__ == "__main__":
    main()

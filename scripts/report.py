#!/usr/bin/env python3
"""
Generate figures and a PDF report from options CSV, calibration JSON, Heston series CSV, and returns CSV.

Outputs to docs/artifacts/ by default:
  - heston_error_heatmap.png (price error in bps across moneyness×tenor)
  - iv_surface.png (market IV scatter by moneyness×tenor)
  - heston_params.png (parameter time series)
  - var_backtest.png (rolling VaR and exceptions)
  - onepager.pdf / twopager.pdf (stitched overview)

Usage:
  python scripts/report.py \
    --options_csv data/options.csv \
    --calib_json docs/artifacts/heston_calib.json \
    --returns_csv data/returns.csv \
    --series_csv docs/artifacts/heston_series.csv \
    --artifacts_dir docs/artifacts
"""
import argparse
import json
import math
import os
import subprocess
import sys

from manifest_utils import ARTIFACTS_ROOT


def ensure_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
        from matplotlib.backends.backend_pdf import PdfPages  # noqa: F401
    except Exception:  # pragma: no cover
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "matplotlib",
                "pandas",
                "numpy",
            ]
        )


def run_cli(args):
    out = subprocess.check_output(args, text=True).strip()
    return out


def price_heston_cli(cli_path, row, calib):
    args = [
        cli_path,
        "heston",
        str(calib["kappa"]),
        str(calib["theta"]),
        str(calib["sigma"]),
        str(calib["rho"]),
        str(calib["v0"]),
        str(row["spot"]),
        str(row["strike"]),
        str(row["rate"]),
        str(row["q"]),
        str(row["maturity_years"]),
        "0",
        "1",
        "0",
        "--analytic",
    ]
    try:
        return float(run_cli(args))
    except Exception:
        return float("nan")


def build_error_heatmap(cli_path, options_csv, calib_json, out_png):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    with open(calib_json, "r") as fh:
        calib = json.load(fh)

    df = pd.read_csv(options_csv)
    df = df[(df["maturity_years"] > 1 / 365.0) & (df["mid"] > 0)]
    df["moneyness"] = df["strike"] / df["spot"]
    # model price
    df["model"] = df.apply(lambda r: price_heston_cli(cli_path, r, calib), axis=1)
    # parity for puts
    df.loc[df["call_put"] == "put", "model"] = (
        df.loc[df["call_put"] == "put", "model"]
        - df.loc[df["call_put"] == "put", "spot"]
        * np.exp(
            -df.loc[df["call_put"] == "put", "q"]
            * df.loc[df["call_put"] == "put", "maturity_years"]
        )
        + df.loc[df["call_put"] == "put", "strike"]
        * np.exp(
            -df.loc[df["call_put"] == "put", "rate"]
            * df.loc[df["call_put"] == "put", "maturity_years"]
        )
    )
    df["err_bps"] = 1e4 * (df["model"] - df["mid"]) / df["spot"]

    # pivot into heatmap grid
    m_bins = np.linspace(0.7, 1.3, 25)
    t_bins = np.linspace(df["maturity_years"].min(), df["maturity_years"].max(), 20)
    H = np.full((len(t_bins) - 1, len(m_bins) - 1), np.nan)
    for i in range(len(t_bins) - 1):
        for j in range(len(m_bins) - 1):
            cell = df[
                (df["maturity_years"] >= t_bins[i])
                & (df["maturity_years"] < t_bins[i + 1])
                & (df["moneyness"] >= m_bins[j])
                & (df["moneyness"] < m_bins[j + 1])
            ]
            if not cell.empty:
                H[i, j] = cell["err_bps"].mean()

    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(
        H,
        aspect="auto",
        origin="lower",
        extent=[m_bins[0], m_bins[-1], t_bins[0], t_bins[-1]],
        cmap="coolwarm",
    )
    ax.set_xlabel("Moneyness K/S")
    ax.set_ylabel("Maturity (years)")
    ax.set_title("Heston price error (bps)")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("bps")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)


def build_iv_surface(options_csv, out_png):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    # derive IV via bisection on call parity
    def bs_call(S, K, r, q, sigma, T):
        if T <= 0 or sigma <= 0:
            return max(0.0, S * np.exp(-q * T) - K * np.exp(-r * T))
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        from math import erf, sqrt

        N1 = 0.5 * (1 + erf(d1 / np.sqrt(2)))
        N2 = 0.5 * (1 + erf(d2 / np.sqrt(2)))
        return S * np.exp(-q * T) * N1 - K * np.exp(-r * T) * N2

    def iv_from_price(S, K, r, q, T, price):
        lo, hi = 1e-6, 5.0
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            val = bs_call(S, K, r, q, mid, T)
            if val > price:
                hi = mid
            else:
                lo = mid
        return 0.5 * (lo + hi)

    df = pd.read_csv(options_csv)
    df = df[(df["maturity_years"] > 1 / 365.0) & (df["mid"] > 0)]
    rows = []
    for _, r in df.iterrows():
        S = r["spot"]
        K = r["strike"]
        rr = r["rate"]
        qq = r["q"]
        T = r["maturity_years"]
        P = r["mid"]
        if r["call_put"] == "put":
            P = P + S * np.exp(-qq * T) - K * np.exp(-rr * T)
        iv = iv_from_price(S, K, rr, qq, T, P)
        rows.append({"moneyness": K / S, "T": T, "iv": iv})
    ivdf = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7, 4))
    sc = ax.scatter(ivdf["moneyness"], ivdf["T"], c=ivdf["iv"], cmap="viridis", s=10)
    ax.set_xlabel("K/S")
    ax.set_ylabel("T (years)")
    ax.set_title("Market IV surface (scatter)")
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("implied vol")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)


def build_param_series(series_csv, out_png):
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.read_csv(series_csv)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
    fig, axes = plt.subplots(3, 2, figsize=(10, 6))
    axes = axes.flatten()
    keys = ["kappa", "theta", "sigma", "rho", "v0", "cost"]
    for ax, k in zip(axes, keys):
        if k in df.columns:
            ax.plot(df["date"] if "date" in df.columns else range(len(df)), df[k])
            ax.set_title(k)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)


def build_var_plot(returns_csv, out_png, alpha=0.99):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    df = pd.read_csv(returns_csv)
    df = df.dropna(subset=["ret"])
    window = 250
    z = 2.3263478740408408
    var = []
    exc = []
    for i in range(len(df)):
        if i < window:
            var.append(float("nan"))
            exc.append(float("nan"))
            continue
        mu = df["ret"].iloc[i - window : i].mean()
        sd = df["ret"].iloc[i - window : i].std()
        v = -(mu - z * sd)
        var.append(v)
        exc.append(1.0 if df["ret"].iloc[i] < -v else 0.0)
    df["var"] = var
    df["exc"] = exc
    # Kupiec/Christoffersen using our CLI risk backtest or local formula
    # Build exception sequence as ints
    exc_seq = [int(x == 1.0) for x in df["exc"].dropna().tolist()]
    try:
        # If pyquant_pricer available, use binding for exact stats
        import pyquant_pricer as qp  # type: ignore

        stats = (
            qp.kupiec_christoffersen(exc_seq, alpha)
            if hasattr(qp, "kupiec_christoffersen")
            else None
        )
    except Exception:
        stats = None
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df["var"], label="VaR (1d, 99%)")
    ax.plot(-df["ret"], alpha=0.5, label="-Return")
    ax.scatter(
        df.index[df["exc"] == 1.0],
        -df["ret"][df["exc"] == 1.0],
        color="red",
        s=8,
        label="Exceptions",
    )
    ax.legend(loc="upper right")
    ax.set_title("VaR backtest (rolling normal)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)
    if stats:
        print(
            "VaR backtest: POF p={:.3g}, IND p={:.3g}, CC p={:.3g}".format(
                stats["p_pof"], stats["p_ind"], stats["p_cc"]
            )
        )


def stitch_pdf(artifacts_dir, images, pdf_name):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    pdf_path = os.path.join(artifacts_dir, pdf_name)
    with PdfPages(pdf_path) as pdf:
        rows = 2
        cols = 2
        fig, axes = plt.subplots(rows, cols, figsize=(11.0, 8.5))
        axes = axes.flatten()
        for ax, img in zip(axes, images):
            if not os.path.exists(img):
                continue
            im = plt.imread(img)
            ax.imshow(im)
            ax.axis("off")
        pdf.savefig(fig)
        plt.close(fig)
    print("wrote", pdf_path)


def main():
    ensure_matplotlib()
    import pandas as pd

    ap = argparse.ArgumentParser()
    ap.add_argument("--options_csv", required=True)
    ap.add_argument("--calib_json", required=True)
    ap.add_argument("--returns_csv", required=True)
    ap.add_argument("--artifacts_dir", default=str(ARTIFACTS_ROOT))
    ap.add_argument("--cli", default=os.path.join("build", "quant_cli"))
    ap.add_argument("--series_csv", required=False)
    args = ap.parse_args()

    os.makedirs(args.artifacts_dir, exist_ok=True)
    heatmap = os.path.join(args.artifacts_dir, "heston_error_heatmap.png")
    build_error_heatmap(args.cli, args.options_csv, args.calib_json, heatmap)

    var_png = os.path.join(args.artifacts_dir, "var_backtest.png")
    build_var_plot(args.returns_csv, var_png)

    iv_png = os.path.join(args.artifacts_dir, "iv_surface.png")
    build_iv_surface(args.options_csv, iv_png)

    series_png = None
    if args.series_csv:
        series_png = os.path.join(args.artifacts_dir, "heston_params.png")
        build_param_series(args.series_csv, series_png)

    # stitch
    images = [heatmap, var_png, iv_png]
    if series_png:
        images.append(series_png)
    stitch_pdf(args.artifacts_dir, images[:4], "onepager.pdf")


if __name__ == "__main__":
    main()

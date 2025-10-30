#!/usr/bin/env python3
"""
Generate a compact Heston parameter time-series plot over multiple trade dates.

The script calibrates each normalized surface (see `scripts/data/schema.md`) in
FAST mode by default, captures the fitted parameters, and writes two artifacts:

  * artifacts/heston/params_series.csv — per-date parameters and fit quality
  * artifacts/heston/params_series.png — line plot showing parameter stability

Example usage:
  ./scripts/heston_series_plot.py --inputs data/normalized/spy_20230601.csv data/samples/spx_20240614_sample.csv --fast
  ./scripts/heston_series_plot.py --pattern 'spx_*.csv' --input-dir data/normalized --fast
"""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from calibrate_heston import CalibrationConfig, calibrate_surface, save_calibration_outputs
from calibrate_heston_series import resolve_inputs
from manifest_utils import describe_inputs, update_run


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate Heston parameter series plot and CSV.")
    ap.add_argument(
        "--inputs",
        nargs="*",
        default=[],
        help="Explicit list of normalized surfaces (date inferred from contents).",
    )
    ap.add_argument(
        "--pattern",
        default="spx_*.csv",
        help="Glob pattern (relative to --input-dir) when --inputs is empty.",
    )
    ap.add_argument(
        "--input-dir",
        default="data/normalized",
        help="Directory to search when using --pattern.",
    )
    ap.add_argument(
        "--output-csv",
        default="artifacts/heston/params_series.csv",
        help="Destination CSV collecting per-date parameters.",
    )
    ap.add_argument(
        "--output-png",
        default="artifacts/heston/params_series.png",
        help="Destination PNG summarising the parameter series.",
    )
    ap.add_argument("--metric", choices=["price", "vol"], default="vol", help="Calibration error metric.")
    ap.add_argument("--fast", action="store_true", help="FAST mode trims strikes/maturities per expiry.")
    ap.add_argument("--seed", type=int, default=41, help="Base seed; incremented per surface.")
    ap.add_argument("--retries", type=int, default=3, help="Random restarts per surface.")
    ap.add_argument("--skip-manifest", action="store_true", help="Suppress manifest logging.")
    return ap.parse_args()


def _plot_params(df: pd.DataFrame, output_png: Path) -> None:
    if df.empty:
        raise ValueError("No calibration rows available for plotting.")

    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    fig, axes = plt.subplots(3, 2, figsize=(10, 8), sharex=True)
    panels = [
        ("kappa", r"$\kappa$"),
        ("theta", r"$\theta$"),
        ("sigma_v", r"$\sigma_v$"),
        ("rho", r"$\rho$"),
        ("v0", r"$v_0$"),
        ("rmspe_vol_pct", "RMSPE (%)"),
    ]
    for ax, (col, label) in zip(axes.flatten(), panels):
        ax.plot(df["date_dt"], df[col], marker="o", linestyle="-", linewidth=1.5)
        ax.set_ylabel(label)
        ax.grid(alpha=0.3, linestyle="--", linewidth=0.6)
    axes[-1][0].set_xlabel("Trade date")
    axes[-1][1].set_xlabel("Trade date")
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    for ax in axes.flatten():
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=180)
    plt.close(fig)


def main() -> None:
    args = _parse_args()
    repo_inputs: List[Path] = resolve_inputs(args.inputs, args.pattern, args.input_dir)
    if len(repo_inputs) < 1:
        raise ValueError("Need at least one normalized surface to build a parameter series.")

    rows = []
    output_dir = Path(args.output_csv).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    per_run_dir = output_dir / "series_runs"
    per_run_dir.mkdir(parents=True, exist_ok=True)

    for idx, csv_path in enumerate(repo_inputs):
        df = pd.read_csv(csv_path)
        config = CalibrationConfig(
            fast=args.fast,
            metric=args.metric,
            seed=args.seed + idx,
            retries=args.retries,
        )
        metrics, surface = calibrate_surface(df, config)
        metrics["input"] = str(csv_path)
        artifacts = save_calibration_outputs(surface, metrics, per_run_dir, args.fast)

        params = metrics["params"]
        trade_date = surface["date"].iloc[0].isoformat()
        rows.append(
            {
                "date": trade_date,
                "input_csv": str(csv_path),
                "fast_mode": bool(args.fast),
                "metric": args.metric,
                "kappa": params["kappa"],
                "theta": params["theta"],
                "sigma_v": params["sigma"],
                "rho": params["rho"],
                "v0": params["v0"],
                "rmse_vol": metrics["rmse_vol"],
                "rmspe_vol_pct": metrics["rmspe_vol_pct"],
                "rmse_price": metrics["rmse_price"],
                "n_obs": metrics["n_obs"],
                "n_strikes": metrics["n_strikes"],
                "n_maturities": metrics["n_maturities"],
                "params_json": str(artifacts["params_path"]),
                "figure_png": str(artifacts["figure_path"]),
                "table_csv": str(artifacts["table_path"]),
            }
        )

    df = pd.DataFrame(rows).sort_values("date")
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    output_png = Path(args.output_png)
    _plot_params(df, output_png)

    command = shlex.join([sys.executable] + sys.argv)
    manifest_entry = {
        "command": command,
        "fast": bool(args.fast),
        "metric": args.metric,
        "seed": args.seed,
        "retries": args.retries,
        "inputs": [str(p) for p in repo_inputs],
        "input_descriptors": describe_inputs(repo_inputs),
        "output_csv": str(output_csv),
        "output_png": str(output_png),
        "num_dates": int(len(df)),
        "dates": df["date"].tolist(),
        "rows": rows,
    }
    if not args.skip_manifest:
        update_run("heston_params_series", manifest_entry)

    print(f"Wrote parameter series CSV -> {output_csv}")
    print(f"Wrote parameter series PNG -> {output_png}")


if __name__ == "__main__":
    main()

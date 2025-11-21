#!/usr/bin/env python3
"""Lightweight BS vs Heston comparison on top of WRDS aggregates."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from manifest_utils import ARTIFACTS_ROOT


WRDS_ROOT = ARTIFACTS_ROOT / "wrds"
PER_DATE_ROOT = WRDS_ROOT / "per_date"


def _concat_csv(files: Iterable[Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in files:
        if path.exists():
            frames.append(pd.read_csv(path))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _bucket_rmse(
    df: pd.DataFrame, error_col: str, weight_col: str | None = None
) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    weights = (
        df[weight_col].astype(float).to_numpy()
        if weight_col and weight_col in df.columns
        else np.ones(len(df), dtype=float)
    )
    errors = df[error_col].astype(float).to_numpy()
    return pd.Series(
        np.sqrt(np.average(np.square(errors), weights=weights)), index=["value"]
    )


def _bucket_mae(
    df: pd.DataFrame, error_col: str, weight_col: str | None = None
) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    weights = (
        df[weight_col].astype(float).to_numpy()
        if weight_col and weight_col in df.columns
        else np.ones(len(df), dtype=float)
    )
    errors = df[error_col].astype(float).to_numpy()
    return pd.Series(np.average(np.abs(errors), weights=weights), index=["value"])


def _load_insample(model: str) -> pd.DataFrame:
    """Load per-row insample surfaces across all dates for a model."""
    filename = "wrds_heston_insample.csv" if model == "heston" else "bs_fit_table.csv"
    files = [p / filename for p in PER_DATE_ROOT.glob("*") if (p / filename).exists()]
    df = _concat_csv(files)
    if df.empty:
        return df
    if "iv_error_vol" not in df.columns and "iv_error_bps" in df.columns:
        df["iv_error_vol"] = df["iv_error_bps"].astype(float) / 1e4
    return df


def _load_oos(model: str) -> pd.DataFrame:
    """Load per-row OOS surfaces across all dates for a model."""
    if model == "heston":
        filename = "oos_pricing_detail.csv"
    else:
        filename = "bs_oos_summary.csv"
    files = [p / filename for p in PER_DATE_ROOT.glob("*") if (p / filename).exists()]
    return _concat_csv(files)


def _load_pnl() -> pd.DataFrame:
    files = [
        p / "delta_hedge_pnl_summary.csv" for p in PER_DATE_ROOT.glob("*")
    ]
    return _concat_csv(files)


def _aggregate_buckets() -> Dict[str, pd.DataFrame]:
    heston_insample = _load_insample("heston")
    bs_insample = _load_insample("bs")

    heston_oos = _load_oos("heston")
    bs_oos = _load_oos("bs")

    pnl = _load_pnl()

    def insample_bucket(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=["tenor_bucket", "iv_rmse_volpts", "price_rmse_ticks"]
            )
        rows = []
        for bucket, g in df.groupby("tenor_bucket", observed=True):
            rows.append(
                {
                    "tenor_bucket": bucket,
                    "iv_rmse_volpts": _bucket_rmse(
                        g, "iv_error_vol", weight_col="quotes"
                    )["value"],
                    "price_rmse_ticks": _bucket_rmse(
                        g, "price_error_ticks", weight_col="quotes"
                    )["value"],
                }
            )
        return pd.DataFrame(rows)

    def oos_bucket(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "trade_date",
                    "tenor_bucket",
                    "iv_mae_bps",
                    "price_mae_ticks",
                    "quotes",
                ]
            )
        rows = []
        for (trade_date, bucket), g in df.groupby(
            ["trade_date", "tenor_bucket"], observed=True
        ):
            rows.append(
                {
                    "trade_date": trade_date,
                    "tenor_bucket": bucket,
                    "iv_mae_bps": _bucket_mae(
                        g, "iv_error_bps", weight_col="quotes"
                    )["value"],
                    "price_mae_ticks": _bucket_mae(
                        g, "price_error_ticks", weight_col="quotes"
                    )["value"],
                    "quotes": g["quotes"].sum(),
                }
            )
        return pd.DataFrame(rows)

    heston_insample_buckets = insample_bucket(heston_insample)
    bs_insample_buckets = insample_bucket(bs_insample)
    heston_oos_buckets = oos_bucket(heston_oos)
    bs_oos_buckets = oos_bucket(bs_oos)

    pnl_bucket = pd.DataFrame()
    if not pnl.empty:
        pnl_bucket = (
            pnl.groupby("tenor_bucket", observed=True)
            .agg(
                pnl_sigma=("pnl_sigma", "mean"),
                count=("count", "sum"),
                mean_ticks=("mean_ticks", "mean"),
            )
            .reset_index()
        )

    return {
        "heston_insample": heston_insample_buckets,
        "bs_insample": bs_insample_buckets,
        "heston_oos": heston_oos_buckets,
        "bs_oos": bs_oos_buckets,
        "pnl": pnl_bucket,
    }


def _merge_comparison(buckets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    base = pd.DataFrame({"tenor_bucket": sorted(set(
        pd.concat(
            [
                buckets.get("heston_insample", pd.DataFrame(columns=["tenor_bucket"])),
                buckets.get("bs_insample", pd.DataFrame(columns=["tenor_bucket"])),
                buckets.get("heston_oos", pd.DataFrame(columns=["tenor_bucket"])),
                buckets.get("bs_oos", pd.DataFrame(columns=["tenor_bucket"])),
                buckets.get("pnl", pd.DataFrame(columns=["tenor_bucket"])),
            ],
            ignore_index=True,
        )["tenor_bucket"].dropna().unique()
    ))})

    insample = base.merge(
        buckets["heston_insample"], on="tenor_bucket", how="left", suffixes=("", "")
    ).rename(
        columns={
            "iv_rmse_volpts": "heston_iv_rmse_volpts",
            "price_rmse_ticks": "heston_price_rmse_ticks",
        }
    )
    insample = insample.merge(
        buckets["bs_insample"],
        on="tenor_bucket",
        how="left",
        suffixes=("", "_bs"),
    ).rename(
        columns={
            "iv_rmse_volpts": "bs_iv_rmse_volpts",
            "price_rmse_ticks": "bs_price_rmse_ticks",
        }
    )

    oos_h = buckets["heston_oos"]
    oos_b = buckets["bs_oos"]
    def _bucket_average(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        cols = [
            "tenor_bucket",
            f"{prefix}_oos_iv_mae_bps",
            f"{prefix}_oos_price_mae_ticks",
        ]
        if df.empty:
            return pd.DataFrame(columns=cols)
        rows = []
        for bucket, g in df.groupby("tenor_bucket", observed=True):
            rows.append(
                {
                    "tenor_bucket": bucket,
                    f"{prefix}_oos_iv_mae_bps": _bucket_mae(
                        g, "iv_mae_bps", weight_col="quotes"
                    )["value"],
                    f"{prefix}_oos_price_mae_ticks": _bucket_mae(
                        g, "price_mae_ticks", weight_col="quotes"
                    )["value"],
                }
            )
        return pd.DataFrame(rows)

    oos = base.merge(
        _bucket_average(oos_h, "heston"), on="tenor_bucket", how="left"
    )
    oos = oos.merge(
        _bucket_average(oos_b, "bs"), on="tenor_bucket", how="left"
    )

    pnl = base.merge(
        buckets["pnl"], on="tenor_bucket", how="left"
    ).rename(columns={"pnl_sigma": "heston_pnl_sigma"})

    combined = (
        insample.merge(oos, on="tenor_bucket", how="outer")
        .merge(pnl, on="tenor_bucket", how="outer")
        .sort_values("tenor_bucket")
    )

    for col in [
        "heston_iv_rmse_volpts",
        "bs_iv_rmse_volpts",
        "heston_price_rmse_ticks",
        "bs_price_rmse_ticks",
        "heston_oos_iv_mae_bps",
        "bs_oos_iv_mae_bps",
        "heston_oos_price_mae_ticks",
        "bs_oos_price_mae_ticks",
    ]:
        if col not in combined.columns:
            combined[col] = np.nan
    combined["delta_iv_rmse_volpts"] = (
        combined["heston_iv_rmse_volpts"] - combined["bs_iv_rmse_volpts"]
    )
    combined["delta_price_rmse_ticks"] = (
        combined["heston_price_rmse_ticks"] - combined["bs_price_rmse_ticks"]
    )
    combined["delta_oos_iv_mae_bps"] = (
        combined["heston_oos_iv_mae_bps"] - combined["bs_oos_iv_mae_bps"]
    )
    combined["delta_oos_price_mae_ticks"] = (
        combined["heston_oos_price_mae_ticks"] - combined["bs_oos_price_mae_ticks"]
    )
    return combined


def _plot_iv_rmse(comp: pd.DataFrame, out_path: Path) -> None:
    df = comp.dropna(subset=["heston_iv_rmse_volpts", "bs_iv_rmse_volpts"])
    if df.empty:
        return
    x = np.arange(len(df))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width / 2, df["bs_iv_rmse_volpts"] * 100, width, label="BS")
    ax.bar(x + width / 2, df["heston_iv_rmse_volpts"] * 100, width, label="Heston")
    ax.set_ylabel("IV RMSE (vol pts)")
    ax.set_title("WRDS – In-sample IV RMSE by tenor")
    ax.set_xticks(x)
    ax.set_xticklabels(df["tenor_bucket"])
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_oos_heatmap(
    oos_h: pd.DataFrame, oos_b: pd.DataFrame, out_path: Path
) -> None:
    if oos_h.empty or oos_b.empty:
        return
    merged = (
        oos_h.merge(
            oos_b,
            on=["trade_date", "tenor_bucket"],
            how="inner",
            suffixes=("_h", "_b"),
        )
        .assign(delta=lambda df: df["iv_mae_bps_h"] - df["iv_mae_bps_b"])
        .sort_values(["trade_date", "tenor_bucket"])
    )
    if merged.empty:
        return
    pivot = merged.pivot(
        index="tenor_bucket", columns="trade_date", values="delta"
    ).sort_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(pivot, aspect="auto", cmap="coolwarm")
    ax.set_title("OOS IV MAE (Heston − BS, bps)")
    ax.set_xlabel("Trade date")
    ax.set_ylabel("Tenor")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(im, ax=ax, label="bps")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_pnl_sigma(comp: pd.DataFrame, out_path: Path) -> None:
    df = comp.dropna(subset=["heston_pnl_sigma"])
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df["tenor_bucket"], df["heston_pnl_sigma"], color="#2ca02c")
    ax.set_ylabel("σ (ticks)")
    ax.set_title("Δ-hedged 1d PnL σ (Heston)")
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def generate_comparison_artifacts(
    artifacts_root: Path = WRDS_ROOT,
    per_date_root: Path = PER_DATE_ROOT,
) -> Dict[str, Path]:
    buckets = _aggregate_buckets()
    comp = _merge_comparison(buckets)
    comp_csv = artifacts_root / "wrds_bs_heston_comparison.csv"
    comp.to_csv(comp_csv, index=False)

    iv_fig = artifacts_root / "wrds_bs_heston_ivrmse.png"
    _plot_iv_rmse(comp, iv_fig)

    heatmap_fig = artifacts_root / "wrds_bs_heston_oos_heatmap.png"
    _plot_oos_heatmap(buckets.get("heston_oos", pd.DataFrame()), buckets.get("bs_oos", pd.DataFrame()), heatmap_fig)

    pnl_fig = artifacts_root / "wrds_bs_heston_pnl_sigma.png"
    _plot_pnl_sigma(comp, pnl_fig)

    return {
        "comparison_csv": comp_csv,
        "ivrmse_fig": iv_fig,
        "oos_heatmap_fig": heatmap_fig,
        "pnl_fig": pnl_fig,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate BS vs Heston comparison from WRDS artifacts."
    )
    ap.add_argument(
        "--wrds-root",
        default=str(WRDS_ROOT),
        help="Directory containing wrds artifacts (default docs/artifacts/wrds)",
    )
    args = ap.parse_args()
    root = Path(args.wrds_root)
    generate_comparison_artifacts(root, root / "per_date")


if __name__ == "__main__":  # pragma: no cover
    main()

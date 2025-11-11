#!/usr/bin/env python3
"""Run the WRDS sample pipeline end-to-end."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (REPO_ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from manifest_utils import ARTIFACTS_ROOT, update_run

from . import calibrate_heston, delta_hedge_pnl, ingest_sppx_surface, oos_pricing


def _next_business_day(trade_date: str) -> str:
    date = pd.to_datetime(trade_date).date()
    while True:
        date += timedelta(days=1)
        if date.weekday() < 5:
            return date.isoformat()


def _plot_wrds_summary(
    surface: pd.DataFrame, oos: pd.DataFrame, pnl: pd.DataFrame, out_path: Path
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    for bucket, group in surface.groupby("tenor_bucket", observed=True):
        axes[0].plot(group["moneyness"], group["mid_iv"], "o-", label=f"{bucket} mkt")
        axes[0].plot(
            group["moneyness"], group["model_iv"], "--", label=f"{bucket} model"
        )
    axes[0].set_title("In-sample IV vs model")
    axes[0].set_xlabel("Moneyness")
    axes[0].set_ylabel("Implied vol (vol pts)")
    axes[0].grid(True, ls=":", alpha=0.4)
    axes[0].legend(fontsize=7, ncol=2)

    if not oos.empty:
        axes[1].bar(oos["tenor_bucket"], oos["iv_mae_bps"], color="#1f77b4")
        axes[1].set_title("Next-day IV MAE (bps)")
        axes[1].set_ylabel("IV MAE (bps)")
        axes2 = axes[1].twinx()
        axes2.plot(
            oos["tenor_bucket"],
            oos["price_mae_ticks"],
            "s--",
            color="#ff7f0e",
            label="Price ticks",
        )
        axes2.set_ylabel("Price MAE (ticks)")
        axes2.legend(loc="upper right", fontsize=7)
    else:
        axes[1].text(0.5, 0.5, "No OOS data", ha="center", va="center")
    axes[1].grid(True, axis="y", ls=":", alpha=0.5)

    if not pnl.empty:
        hist_data = pnl.loc[
            pnl.index.repeat(pnl["quotes"].clip(lower=1).astype(int)), "pnl_per_tick"
        ]
        axes[2].hist(hist_data, bins=15, color="#2ca02c", alpha=0.8)
        axes[2].set_title("Delta-hedged 1d PnL (ticks)")
    else:
        axes[2].text(0.5, 0.5, "No PnL data", ha="center", va="center")
    axes[2].set_xlabel("PnL (ticks)")
    axes[2].grid(True, ls=":", alpha=0.4)

    fig.suptitle("WRDS Heston: in-sample vs OOS diagnostics")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_insample_surface(surface: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    for bucket, group in surface.groupby("tenor_bucket", observed=True):
        ax.plot(group["moneyness"], group["mid_iv"], "o-", label=f"{bucket} mkt")
        ax.plot(group["moneyness"], group["model_iv"], "--", label=f"{bucket} model")
    ax.set_title("WRDS Heston – in-sample IV parity")
    ax.set_xlabel("Moneyness")
    ax.set_ylabel("Implied vol (vol pts)")
    ax.grid(True, ls=":", alpha=0.4)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_oos_summary(oos: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    if oos.empty:
        ax.text(0.5, 0.5, "No OOS data", ha="center", va="center")
    else:
        ax.bar(
            oos["tenor_bucket"], oos["iv_mae_bps"], color="#1f77b4", label="IV (bps)"
        )
        ax.set_ylabel("IV MAE (bps)")
        ax2 = ax.twinx()
        ax2.plot(
            oos["tenor_bucket"],
            oos["price_mae_ticks"],
            "s--",
            color="#ff7f0e",
            label="Price ticks",
        )
        ax2.set_ylabel("Price MAE (ticks)")
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=8)
    ax.set_title("WRDS Heston – next-day OOS errors")
    ax.set_xlabel("Tenor bucket")
    ax.grid(True, axis="y", ls=":", alpha=0.4)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_hedge_distribution(pnl_detail: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    if pnl_detail.empty:
        ax.text(0.5, 0.5, "No hedge data", ha="center", va="center")
    else:
        hist_data = pnl_detail.loc[
            pnl_detail.index.repeat(pnl_detail["quotes"].clip(lower=1).astype(int)),
            "pnl_per_tick",
        ]
        ax.hist(hist_data, bins=20, color="#2ca02c", alpha=0.85)
    ax.set_title("WRDS Heston – Δ-hedged 1d PnL (ticks)")
    ax.set_xlabel("PnL (ticks)")
    ax.set_ylabel("Frequency")
    ax.grid(True, ls=":", alpha=0.4)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_multi_date_summary(
    pricing: pd.DataFrame, oos: pd.DataFrame, pnl: pd.DataFrame, out_path: Path
) -> None:
    if pricing.empty:
        return
    color_map = {"stress": "#d62728", "calm": "#1f77b4", "unknown": "#7f7f7f"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    pricing_sorted = pricing.sort_values("trade_date")
    labels = pricing_sorted["label"].fillna(pricing_sorted["trade_date"])
    colors = pricing_sorted["regime"].map(color_map).fillna(color_map["unknown"])
    axes[0].bar(labels, pricing_sorted["iv_rmse_volpts_vega_wt"] * 100.0, color=colors)
    axes[0].set_title("Vega-wtd IV RMSE")
    axes[0].set_ylabel("vol pts")
    for tick in axes[0].get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")
    axes[0].grid(True, axis="y", ls=":", alpha=0.4)

    if oos.empty:
        axes[1].text(0.5, 0.5, "No OOS data", ha="center", va="center")
    else:
        pivot = oos.pivot_table(
            index="tenor_bucket",
            columns="trade_date",
            values="iv_mae_bps",
            observed=True,
        ).sort_index()
        im = axes[1].imshow(pivot, aspect="auto", cmap="viridis")
        axes[1].set_title("OOS IV MAE (bps)")
        axes[1].set_xlabel("Trade date")
        axes[1].set_ylabel("Tenor")
        axes[1].set_xticks(range(len(pivot.columns)))
        axes[1].set_xticklabels(pivot.columns, rotation=45, ha="right")
        axes[1].set_yticks(range(len(pivot.index)))
        axes[1].set_yticklabels(pivot.index)
        fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04, label="bps")

    if pnl.empty:
        axes[2].text(0.5, 0.5, "No hedge data", ha="center", va="center")
    else:
        pnl_avg = (
            pnl.groupby(
                ["trade_date", "regime", "label"], observed=True, as_index=False
            )
            .agg(mean_ticks=("mean_ticks", "mean"), pnl_sigma=("pnl_sigma", "mean"))
            .sort_values("trade_date")
        )
        pnl_colors = pnl_avg["regime"].map(color_map).fillna(color_map["unknown"])
        bars = axes[2].bar(
            pnl_avg["label"].fillna(pnl_avg["trade_date"]),
            pnl_avg["mean_ticks"],
            color=pnl_colors,
            yerr=pnl_avg["pnl_sigma"],
            capsize=4,
        )
        axes[2].set_title("Δ-hedged mean ticks ± σ")
        axes[2].set_ylabel("ticks")
        for tick in axes[2].get_xticklabels():
            tick.set_rotation(30)
            tick.set_ha("right")
        axes[2].axhline(0.0, color="#444444", linewidth=1)
        axes[2].grid(True, axis="y", ls=":", alpha=0.4)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _load_dateset_payload(path: Path) -> Dict[str, object]:
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                f"{path} is not valid JSON; install PyYAML to parse YAML datesets"
            ) from exc
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise RuntimeError(f"{path} must contain a mapping with a 'dates' field")
        return data


def run(
    symbol: str,
    trade_date: str,
    next_trade_date: str | None,
    use_sample: bool,
    fast: bool,
    *,
    output_dir: Path | None = None,
    label: str | None = None,
    regime: str | None = None,
) -> Dict[str, object]:
    out_dir = output_dir or (ARTIFACTS_ROOT / "wrds")
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_today, source_today = ingest_sppx_surface.load_surface(
        symbol, trade_date, force_sample=use_sample
    )
    raw_next, source_next = ingest_sppx_surface.load_surface(
        symbol, next_trade_date, force_sample=use_sample
    )

    agg_today = ingest_sppx_surface.aggregate_surface(raw_today)
    try:
        agg_next = ingest_sppx_surface.aggregate_surface(raw_next)
    except Exception:
        agg_next = pd.DataFrame()

    today_csv = out_dir / f"{symbol.lower()}_{trade_date}_surface.csv"
    next_csv = out_dir / f"{symbol.lower()}_{next_trade_date}_surface.csv"
    ingest_sppx_surface.write_surface(today_csv, agg_today)
    ingest_sppx_surface.write_surface(next_csv, agg_next)

    config = calibrate_heston.CalibrationConfig(
        fast=fast,
        max_evals=120 if fast else 220,
        bootstrap_samples=60 if fast else 150,
        rng_seed=19,
    )
    calib = calibrate_heston.calibrate(agg_today, config)
    ci = calibrate_heston.bootstrap_confidence_intervals(
        agg_today, calib["params"], config
    )

    fit_csv = out_dir / "heston_fit_table.csv"
    fit_json = out_dir / "heston_fit.json"
    fit_fig = out_dir / "heston_fit.png"
    calibrate_heston.write_tables(fit_csv, calib["surface"])
    metric_keys = (
        "iv_rmse_volpts_vega_wt",
        "iv_mae_volpts_vega_wt",
        "iv_p90_bps",
        "price_rmse_ticks",
    )
    fit_metrics = {key: float(calib[key]) for key in metric_keys}
    summary_payload = {
        "trade_date": trade_date,
        "next_trade_date": next_trade_date,
        "label": label,
        "regime": regime,
        "params": calib["params"],
        **fit_metrics,
        "bootstrap_ci": {k: list(v) for k, v in ci.items()},
        "source_today": source_today,
        "source_next": source_next,
    }

    oos_detail_csv = out_dir / "oos_pricing_detail.csv"
    oos_summary_csv = out_dir / "oos_pricing_summary.csv"
    if agg_next.empty:
        oos_detail = pd.DataFrame(
            columns=[
                "symbol",
                "trade_date",
                "tenor_bucket",
                "moneyness",
                "mid_iv",
                "model_iv",
                "iv_error_bps",
                "mid_price",
                "model_price",
                "price_error_ticks",
                "quotes",
            ]
        )
        oos_summary = pd.DataFrame(
            columns=["tenor_bucket", "mae_iv_bps", "mae_price_ticks", "quotes"]
        )
    else:
        oos_detail, oos_summary, oos_metrics = oos_pricing.evaluate(
            agg_next, calib["params"]
        )
    if agg_next.empty:
        oos_metrics = calibrate_heston.compute_oos_iv_metrics(oos_detail)
    oos_pricing.write_outputs(oos_detail_csv, oos_summary_csv, oos_detail, oos_summary)

    pnl_detail_csv = out_dir / "delta_hedge_pnl.csv"
    pnl_summary_csv = out_dir / "delta_hedge_pnl_summary.csv"
    pnl_detail, pnl_summary = delta_hedge_pnl.simulate(agg_today, agg_next)
    delta_hedge_pnl.write_outputs(
        pnl_detail_csv, pnl_summary_csv, pnl_detail, pnl_summary
    )

    summary_fig = out_dir / "heston_wrds_summary.png"
    _plot_wrds_summary(calib["surface"], oos_summary, pnl_detail, summary_fig)

    insample_cols = [
        "symbol",
        "trade_date",
        "tenor_bucket",
        "moneyness",
        "ttm_years",
        "mid_iv",
        "model_iv",
        "iv_error_bps",
        "mid_price",
        "model_price",
        "price_error_ticks",
        "quotes",
    ]
    insample_csv = out_dir / "wrds_heston_insample.csv"
    calib["surface"][insample_cols].to_csv(insample_csv, index=False)
    insample_fig = out_dir / "wrds_heston_insample.png"
    _plot_insample_surface(calib["surface"], insample_fig)

    oos_csv = out_dir / "wrds_heston_oos.csv"
    oos_summary.to_csv(oos_csv, index=False)
    oos_fig = out_dir / "wrds_heston_oos.png"
    _plot_oos_summary(oos_summary, oos_fig)

    hedge_csv = out_dir / "wrds_heston_hedge.csv"
    pnl_summary.to_csv(hedge_csv, index=False)
    hedge_fig = out_dir / "wrds_heston_hedge.png"
    _plot_hedge_distribution(pnl_detail, hedge_fig)

    summary_payload.update(oos_metrics)
    calibrate_heston.write_summary(fit_json, summary_payload)
    calibrate_heston.plot_fit(calib["surface"], calib["params"], fit_metrics, fit_fig)
    calibrate_heston.record_manifest(fit_json, summary_payload, fit_csv, fit_fig)

    update_run(
        "wrds_pipeline",
        {
            "symbol": symbol,
            "trade_date": trade_date,
            "next_trade_date": next_trade_date,
            "label": label,
            "regime": regime,
            "source_today": source_today,
            "source_next": source_next,
            "surface_today": str(today_csv),
            "surface_next": str(next_csv),
            "fit_table": str(fit_csv),
            "fit_json": str(fit_json),
            "fit_fig": str(fit_fig),
            "oos_detail": str(oos_detail_csv),
            "oos_summary": str(oos_summary_csv),
            "pnl_detail": str(pnl_detail_csv),
            "pnl_summary": str(pnl_summary_csv),
            "summary_fig": str(summary_fig),
            "wrds_heston_insample_csv": str(insample_csv),
            "wrds_heston_insample_fig": str(insample_fig),
            "wrds_heston_oos_csv": str(oos_csv),
            "wrds_heston_oos_fig": str(oos_fig),
            "wrds_heston_hedge_csv": str(hedge_csv),
            "wrds_heston_hedge_fig": str(hedge_fig),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        append=True,
    )

    return {
        "trade_date": trade_date,
        "next_trade_date": next_trade_date,
        "label": label,
        "regime": regime,
        "summary": summary_payload,
        "oos_summary": oos_summary.copy(),
        "pnl_summary": pnl_summary.copy(),
        "artifacts": {
            "surface_today": today_csv,
            "surface_next": next_csv,
            "fit_json": fit_json,
            "summary_fig": summary_fig,
        },
    }


def run_dateset(
    symbol: str, dateset_path: Path, use_sample: bool, fast: bool
) -> Dict[str, Path]:
    payload = _load_dateset_payload(dateset_path)
    entries = payload.get("dates", [])
    if not entries:
        raise RuntimeError(f"{dateset_path} does not contain any dates")
    per_date_root = ARTIFACTS_ROOT / "wrds" / "per_date"
    per_date_root.mkdir(parents=True, exist_ok=True)
    agg_dir = ARTIFACTS_ROOT / "wrds"
    agg_dir.mkdir(parents=True, exist_ok=True)

    pricing_rows = []
    oos_rows = []
    pnl_rows = []

    for entry in entries:
        trade_date = entry["trade_date"]
        next_trade_date = entry.get("next_trade_date") or _next_business_day(
            entry["trade_date"]
        )
        label = entry.get("label")
        regime = entry.get("regime")
        comment = entry.get("comment")
        per_date_dir = per_date_root / trade_date
        try:
            result = run(
                symbol,
                trade_date,
                next_trade_date,
                use_sample,
                fast,
                output_dir=per_date_dir,
                label=label,
                regime=regime,
            )
        except Exception as exc:  # pragma: no cover
            print(f"[wrds_pipeline] {trade_date} failed: {exc}")
            pricing_rows.append(
                {
                    "trade_date": trade_date,
                    "next_trade_date": next_trade_date,
                    "label": label,
                    "regime": regime,
                    "comment": comment,
                    "status": "error",
                    "iv_rmse_volpts_vega_wt": np.nan,
                    "iv_mae_volpts_vega_wt": np.nan,
                    "iv_p90_bps": np.nan,
                    "price_rmse_ticks": np.nan,
                    "iv_mae_bps": np.nan,
                    "price_mae_ticks": np.nan,
                    "error": str(exc),
                }
            )
            continue
        summary = result["summary"]
        oos_df = result["oos_summary"].copy()
        if not oos_df.empty:
            weights = np.asarray(oos_df["quotes"].clip(lower=1), dtype=np.float64)
            price_mae_ticks = float(
                np.average(oos_df["price_mae_ticks"], weights=weights)
            )
        else:
            price_mae_ticks = float("nan")
        pricing_rows.append(
            {
                "trade_date": summary["trade_date"],
                "next_trade_date": summary["next_trade_date"],
                "label": summary.get("label"),
                "regime": summary.get("regime"),
                "comment": comment,
                "status": "ok",
                "source_today": summary.get("source_today"),
                "source_next": summary.get("source_next"),
                "iv_rmse_volpts_vega_wt": summary["iv_rmse_volpts_vega_wt"],
                "iv_mae_volpts_vega_wt": summary["iv_mae_volpts_vega_wt"],
                "iv_p90_bps": summary["iv_p90_bps"],
                "price_rmse_ticks": summary["price_rmse_ticks"],
                "iv_mae_bps": summary.get("iv_mae_bps"),
                "price_mae_ticks": price_mae_ticks,
            }
        )

        if not oos_df.empty:
            oos_df["trade_date"] = summary["trade_date"]
            oos_df["label"] = summary.get("label")
            oos_df["regime"] = summary.get("regime")
            oos_rows.append(oos_df)

        pnl_df = result["pnl_summary"].copy()
        if not pnl_df.empty:
            pnl_df["trade_date"] = summary["trade_date"]
            pnl_df["label"] = summary.get("label")
            pnl_df["regime"] = summary.get("regime")
            pnl_rows.append(pnl_df)

    pricing_df = pd.DataFrame(pricing_rows)
    pricing_csv = agg_dir / "wrds_agg_pricing.csv"
    pricing_df.to_csv(pricing_csv, index=False)

    if oos_rows:
        oos_df = pd.concat(oos_rows, ignore_index=True)
    else:
        oos_df = pd.DataFrame(
            columns=[
                "trade_date",
                "label",
                "regime",
                "tenor_bucket",
                "iv_mae_bps",
                "price_mae_ticks",
                "quotes",
            ]
        )
    oos_csv = agg_dir / "wrds_agg_oos.csv"
    oos_df.to_csv(oos_csv, index=False)

    if pnl_rows:
        pnl_df = pd.concat(pnl_rows, ignore_index=True)
    else:
        pnl_df = pd.DataFrame(
            columns=[
                "trade_date",
                "label",
                "regime",
                "tenor_bucket",
                "mean_pnl",
                "mean_ticks",
                "pnl_sigma",
                "count",
            ]
        )
    pnl_csv = agg_dir / "wrds_agg_pnl.csv"
    pnl_df.to_csv(pnl_csv, index=False)

    multi_fig = agg_dir / "wrds_multi_date_summary.png"
    _plot_multi_date_summary(pricing_df, oos_df, pnl_df, multi_fig)

    update_run(
        "wrds_dateset",
        {
            "symbol": symbol,
            "dateset": str(dateset_path),
            "pricing_csv": str(pricing_csv),
            "oos_csv": str(oos_csv),
            "pnl_csv": str(pnl_csv),
            "summary_fig": str(multi_fig),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        append=True,
    )

    return {
        "pricing_csv": pricing_csv,
        "oos_csv": oos_csv,
        "pnl_csv": pnl_csv,
        "summary_fig": multi_fig,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--trade-date", default="2024-06-14")
    ap.add_argument("--next-trade-date", default=None)
    ap.add_argument("--use-sample", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument(
        "--dateset",
        default=None,
        help="Path to a YAML/JSON file listing trade dates to batch-process",
    )
    args = ap.parse_args()
    next_trade = args.next_trade_date or _next_business_day(args.trade_date)
    use_sample = args.use_sample or not ingest_sppx_surface.has_wrds_credentials()
    if args.dateset:
        dateset_path = Path(args.dateset)
        if not dateset_path.is_absolute():
            dateset_path = REPO_ROOT / dateset_path
        run_dateset(args.symbol.upper(), dateset_path, use_sample, args.fast)
    else:
        run(args.symbol.upper(), args.trade_date, next_trade, use_sample, args.fast)


if __name__ == "__main__":  # pragma: no cover
    main()

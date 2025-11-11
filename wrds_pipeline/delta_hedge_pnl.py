#!/usr/bin/env python3
"""Delta-hedged 1-day PnL simulation."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .bs_utils import bs_delta_call


def simulate(today: pd.DataFrame, tomorrow: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    merged = pd.merge(
        today,
        tomorrow,
        on=["tenor_bucket", "moneyness"],
        suffixes=("_t", "_t1"),
    )
    if merged.empty:
        detail_cols = ["tenor_bucket", "moneyness", "pnl", "pnl_per_tick", "quotes"]
        summary_cols = ["tenor_bucket", "mean_pnl", "mean_ticks", "pnl_sigma", "count"]
        return pd.DataFrame(columns=detail_cols), pd.DataFrame(columns=summary_cols)

    spot_t = float(today["spot"].mean())
    spot_t1 = float(tomorrow["spot"].mean())
    spot_change = spot_t1 - spot_t

    def _delta(row) -> float:
        return bs_delta_call(
            spot=spot_t,
            strike=float(row["strike_t"]),
            rate=float(row["rate_t"]),
            div=float(row["dividend_t"]),
            vol=float(row["mid_iv_t"]),
            T=float(row["ttm_years_t"]),
        )

    merged["delta"] = merged.apply(_delta, axis=1)
    merged["pnl"] = (merged["mid_price_t1"] - merged["mid_price_t"]) - merged["delta"] * spot_change
    merged["pnl_per_tick"] = merged["pnl"] / 0.05
    merged["quotes"] = merged["quotes_t"]

    detail = merged[["tenor_bucket", "moneyness", "pnl", "pnl_per_tick", "quotes"]].copy()

    exploded = detail.loc[detail.index.repeat(detail["quotes"].clip(lower=1).astype(int))].reset_index(drop=True)
    if exploded.empty:
        summary = pd.DataFrame(columns=["tenor_bucket", "mean_pnl", "mean_ticks", "pnl_sigma", "count"])
    else:
        summary = (
            exploded.groupby("tenor_bucket", as_index=False, observed=True)
            .agg(
                mean_pnl=("pnl", "mean"),
                mean_ticks=("pnl_per_tick", "mean"),
                pnl_sigma=("pnl_per_tick", "std"),
                count=("pnl", "size"),
            )
        )
    for col in ("mean_pnl", "mean_ticks", "pnl_sigma"):
        summary[col] = summary[col].fillna(0.0)
    return detail, summary


def write_outputs(detail_csv: Path, summary_csv: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    detail_csv.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(detail_csv, index=False)
    summary.to_csv(summary_csv, index=False)

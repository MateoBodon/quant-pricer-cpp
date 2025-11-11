#!/usr/bin/env python3
"""Out-of-sample pricing diagnostics."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .calibrate_heston import apply_model, compute_oos_iv_metrics

TICK_SIZE = 0.05


def evaluate(oos_surface: pd.DataFrame, params: Dict[str, float]) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    modeled = apply_model(oos_surface.copy(), params)
    modeled["abs_iv_bps"] = modeled["iv_error_bps"].abs()
    modeled["abs_price_ticks"] = modeled["price_error_ticks"].abs()
    summary = (
        modeled.groupby("tenor_bucket", as_index=False, observed=True)
        .agg(
            mae_iv_bps=("abs_iv_bps", "mean"),
            mae_price_ticks=("abs_price_ticks", "mean"),
            quotes=("quotes", "sum"),
        )
        .sort_values("tenor_bucket")
    )
    metrics = compute_oos_iv_metrics(modeled)
    return modeled, summary, metrics


def write_outputs(detail_csv: Path, summary_csv: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    detail_csv.parent.mkdir(parents=True, exist_ok=True)
    detail_cols = [
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
    detail[detail_cols].to_csv(detail_csv, index=False)
    summary.to_csv(summary_csv, index=False)

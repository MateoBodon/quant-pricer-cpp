#!/usr/bin/env python3
"""Out-of-sample pricing diagnostics."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .asof_checks import assert_quote_date_matches
from .calibrate_heston import apply_model, compute_oos_iv_metrics, _vega_quote_weights

TICK_SIZE = 0.05


def evaluate(
    oos_surface: pd.DataFrame,
    params: Dict[str, float],
    *,
    expected_quote_date: str | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    if expected_quote_date is not None:
        assert_quote_date_matches(
            oos_surface, expected_date=expected_quote_date, context="oos"
        )
    modeled = apply_model(oos_surface.copy(), params)
    # Drop rows where the model produced NaN / inf so aggregates remain meaningful.
    mask = modeled[["iv_error_bps", "price_error_ticks"]].replace([float("inf"), -float("inf")], float("nan")).notnull().all(axis=1)
    modeled = modeled[mask].copy()
    modeled["abs_iv_bps"] = modeled["iv_error_bps"].abs()
    modeled["abs_price_ticks"] = modeled["price_error_ticks"].abs()
    modeled["weight"] = _vega_quote_weights(modeled, default=1.0)
    summary = []
    for bucket, group in modeled.groupby("tenor_bucket", observed=True):
        weights = group["weight"].to_numpy(np.float64)
        summary.append(
            {
                "tenor_bucket": bucket,
                "iv_mae_bps": float(np.average(group["abs_iv_bps"], weights=weights)),
                "price_mae_ticks": float(
                    np.average(group["abs_price_ticks"], weights=weights)
                ),
                "quotes": group["quotes"].sum(),
                "weight": float(weights.sum()),
            }
        )
    summary = pd.DataFrame(summary).sort_values("tenor_bucket")
    metrics = compute_oos_iv_metrics(modeled)
    return modeled, summary, metrics


def write_outputs(
    detail_csv: Path, summary_csv: Path, detail: pd.DataFrame, summary: pd.DataFrame
) -> None:
    detail_csv.parent.mkdir(parents=True, exist_ok=True)
    detail_cols = [
        "symbol",
        "trade_date",
        "tenor_bucket",
        "moneyness",
        "vega",
        "mid_iv",
        "model_iv",
        "iv_error_bps",
        "mid_price",
        "model_price",
        "price_error_ticks",
        "quotes",
        "weight",
    ]
    detail[detail_cols].to_csv(detail_csv, index=False)
    summary.to_csv(summary_csv, index=False)

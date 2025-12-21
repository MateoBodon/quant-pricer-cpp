#!/usr/bin/env python3
"""Black–Scholes baseline calibration for WRDS surfaces.

For each tenor bucket, estimate a single BS volatility via vega-weighted
least squares in IV space (closed-form weighted mean). Then compute the
same aggregate metrics used by the Heston pipeline so we can compare
baseline vs. Heston.
"""
from __future__ import annotations

import dataclasses
from typing import Dict

import numpy as np
import pandas as pd

from . import calibrate_heston
from .bs_utils import bs_call, bs_delta_call, bs_vega

TICK_SIZE = calibrate_heston.TICK_SIZE


@dataclasses.dataclass
class BsFit:
    surface: pd.DataFrame
    metrics: Dict[str, float]


def _weighted_mean_iv(group: pd.DataFrame) -> float:
    weights = calibrate_heston._vega_quote_weights(group)
    ivs = group["mid_iv"].to_numpy(np.float64)
    return float(np.average(ivs, weights=weights))


def _apply_bs_surface(surface: pd.DataFrame) -> pd.DataFrame:
    out = surface.copy()
    vols = (
        out.groupby("tenor_bucket", observed=True)
        .apply(_weighted_mean_iv)
        .rename("fit_vol")
    )
    out = out.merge(vols, on="tenor_bucket", how="left")
    prices = []
    deltas = []
    for _, row in out.iterrows():
        vol = float(row["fit_vol"])
        price = bs_call(
            float(row["spot"]),
            float(row["strike"]),
            float(row["rate"]),
            float(row["dividend"]),
            vol,
            float(row["ttm_years"]),
        )
        delta = bs_delta_call(
            float(row["spot"]),
            float(row["strike"]),
            float(row["rate"]),
            float(row["dividend"]),
            vol,
            float(row["ttm_years"]),
        )
        prices.append(price)
        deltas.append(delta)
    out["model_price"] = prices
    out["model_iv"] = out["fit_vol"]
    out["iv_error_vol"] = out["model_iv"] - out["mid_iv"]
    out["iv_error_bps"] = out["iv_error_vol"] * 1e4
    out["price_error_ticks"] = (out["model_price"] - out["mid_price"]) / TICK_SIZE
    out["model_delta"] = deltas
    out["weight"] = calibrate_heston._vega_quote_weights(out)
    return out


def fit_bs(surface: pd.DataFrame) -> BsFit:
    fitted = _apply_bs_surface(surface)
    metrics = calibrate_heston.compute_insample_metrics(fitted)
    return BsFit(fitted, metrics)


def evaluate_oos(oos_surface: pd.DataFrame, fit_vols: pd.Series) -> pd.DataFrame:
    if oos_surface.empty:
        return pd.DataFrame(
            columns=oos_surface.columns.tolist()
            + ["model_price", "model_iv", "iv_error_bps", "price_error_ticks"]
        )
    out = oos_surface.copy()
    out = out.merge(fit_vols.rename("fit_vol"), on="tenor_bucket", how="left")
    out["fit_vol"] = out["fit_vol"].ffill()
    prices = []
    for _, row in out.iterrows():
        vol = float(row["fit_vol"])
        price = bs_call(
            float(row["spot"]),
            float(row["strike"]),
            float(row["rate"]),
            float(row["dividend"]),
            vol,
            float(row["ttm_years"]),
        )
        prices.append(price)
    out["model_price"] = prices
    out["model_iv"] = out["fit_vol"]
    out["iv_error_bps"] = (out["model_iv"] - out["mid_iv"]) * 1e4
    out["price_error_ticks"] = (out["model_price"] - out["mid_price"]) / TICK_SIZE
    out["weight"] = calibrate_heston._vega_quote_weights(out)
    return out


def summarize_oos(oos_surface: pd.DataFrame) -> Dict[str, float]:
    if oos_surface.empty:
        return {"iv_mae_bps": 0.0, "price_mae_ticks": 0.0}
    weights = calibrate_heston._vega_quote_weights(oos_surface)
    iv_mae_bps = float(np.average(np.abs(oos_surface["iv_error_bps"]), weights=weights))
    price_mae_ticks = float(
        np.average(np.abs(oos_surface["price_error_ticks"]), weights=weights)
    )
    return {"iv_mae_bps": iv_mae_bps, "price_mae_ticks": price_mae_ticks}

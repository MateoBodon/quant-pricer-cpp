#!/usr/bin/env python3
"""Heston calibration utilities for WRDS aggregate surfaces."""
from __future__ import annotations

import dataclasses
import json
import math
import random
from pathlib import Path
from typing import Dict, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import update_run
from scipy.optimize import least_squares

from .bs_utils import bs_call, bs_delta_call, bs_vega, implied_vol_from_price

Params = Tuple[float, float, float, float, float]  # kappa, theta, sigma, rho, v0
TICK_SIZE = 0.05
LOWER_BOUNDS = np.array([0.1, 0.001, 0.05, -0.999, 0.001], dtype=float)
UPPER_BOUNDS = np.array([5.0, 0.5, 2.5, 0.999, 0.5], dtype=float)
POSITIVE_IDX = [0, 1, 2, 4]


def _heston_characteristic(phi, T, params: Params, r, q, log_spot, j: int):
    kappa, theta, sigma, rho, v0 = params
    u = 0.5 if j == 1 else -0.5
    b = kappa - rho * sigma if j == 1 else kappa
    a = kappa * theta
    phi = np.asarray(phi, dtype=np.complex128)
    i = 1j
    d = np.sqrt(
        (rho * sigma * i * phi - b) ** 2
        - sigma * sigma * (2.0 * u * i * phi - phi * phi)
    )
    g = (b - rho * sigma * i * phi + d) / (b - rho * sigma * i * phi - d + 1e-16)
    exp_dt = np.exp(-d * T)
    log_term = np.log((1.0 - g * exp_dt) / (1.0 - g + 1e-16))
    C = (r - q) * i * phi * T + (a / (sigma * sigma)) * (
        (b - rho * sigma * i * phi + d) * T - 2.0 * log_term
    )
    D = ((b - rho * sigma * i * phi + d) / (sigma * sigma)) * (
        (1.0 - exp_dt) / (1.0 - g * exp_dt + 1e-16)
    )
    return np.exp(C + D * v0 + i * phi * log_spot)


def heston_call_price(
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Params,
    n_points: int = 256,
    phi_max: float = 120.0,
) -> float:
    if T <= 0.0:
        return max(spot - strike, 0.0)
    log_spot = math.log(spot)
    log_strike = math.log(strike)
    phis = np.linspace(1e-5, phi_max, n_points, dtype=np.float64)
    cf1 = _heston_characteristic(phis, T, params, rate, div, log_spot, 1)
    cf2 = _heston_characteristic(phis, T, params, rate, div, log_spot, 2)
    exp_term = np.exp(-1j * phis * log_strike)
    denom = 1j * phis
    integrand1 = np.real(exp_term * cf1 / denom)
    integrand2 = np.real(exp_term * cf2 / denom)
    p1 = 0.5 + (1.0 / math.pi) * np.trapz(integrand1, phis)
    p2 = 0.5 + (1.0 / math.pi) * np.trapz(integrand2, phis)
    return spot * math.exp(-div * T) * p1 - strike * math.exp(-rate * T) * p2


def _model_iv(row: pd.Series, params: Params) -> Tuple[float, float]:
    price = heston_call_price(
        spot=float(row["spot"]),
        strike=float(row["strike"]),
        rate=float(row["rate"]),
        div=float(row["dividend"]),
        T=float(row["ttm_years"]),
        params=params,
    )
    iv = implied_vol_from_price(
        price,
        float(row["spot"]),
        float(row["strike"]),
        float(row["rate"]),
        float(row["dividend"]),
        float(row["ttm_years"]),
        option="call",
    )
    return price, iv


@dataclasses.dataclass
class CalibrationConfig:
    fast: bool = False
    max_evals: int = 200
    bootstrap_samples: int = 120
    rng_seed: int = 7


def _positive_weights(values, default: float = 1.0) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).copy()
    if arr.size == 0:
        return np.asarray([default], dtype=np.float64)
    bad = ~np.isfinite(arr) | (arr <= 0)
    if bad.any():
        arr[bad] = default
    if float(arr.sum()) <= 0.0:
        arr[:] = default
    return arr


def _weighted_percentile(
    values: np.ndarray, weights: np.ndarray, percentile: float
) -> float:
    if values.size == 0:
        return 0.0
    percentile = np.clip(percentile, 0.0, 1.0)
    order = np.argsort(values)
    sorted_vals = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    cutoff = percentile * sorted_weights.sum()
    idx = np.searchsorted(cumulative, cutoff, side="left")
    idx = min(idx, len(sorted_vals) - 1)
    return float(sorted_vals[idx])


def compute_insample_metrics(surface: pd.DataFrame) -> Dict[str, float]:
    iv_error_vol = (surface["model_iv"] - surface["mid_iv"]).to_numpy(np.float64)
    default_weights = np.ones(len(surface), dtype=np.float64)
    weights = _positive_weights(surface.get("vega", default_weights))
    abs_iv = np.abs(iv_error_vol)
    iv_rmse_volpts_vega_wt = float(
        np.sqrt(np.average(np.square(iv_error_vol), weights=weights))
    )
    iv_mae_volpts_vega_wt = float(np.average(abs_iv, weights=weights))
    iv_p90_bps = _weighted_percentile(abs_iv * 1e4, weights, 0.9)
    price_rmse_ticks = float(np.sqrt(np.mean(np.square(surface["price_error_ticks"]))))
    return {
        "iv_rmse_volpts_vega_wt": iv_rmse_volpts_vega_wt,
        "iv_mae_volpts_vega_wt": iv_mae_volpts_vega_wt,
        "iv_p90_bps": iv_p90_bps,
        "price_rmse_ticks": price_rmse_ticks,
    }


def compute_oos_iv_metrics(surface: pd.DataFrame) -> Dict[str, float]:
    if surface.empty:
        return {
            "iv_mae_bps": 0.0,
        }
    default_weights = np.ones(len(surface), dtype=np.float64)
    weights = _positive_weights(surface.get("quotes", default_weights))
    iv_error_bps = surface["iv_error_bps"].to_numpy(np.float64)
    iv_mae_bps = float(np.average(np.abs(iv_error_bps), weights=weights))
    return {
        "iv_mae_bps": iv_mae_bps,
    }


def _objective(params_vec: np.ndarray, surface: pd.DataFrame) -> np.ndarray:
    kappa, theta, sigma, rho, v0 = params_vec
    params: Params = (
        max(kappa, 1e-4),
        max(theta, 1e-6),
        max(sigma, 1e-4),
        np.clip(rho, -0.999, 0.999),
        max(v0, 1e-6),
    )
    residuals = []
    for _, row in surface.iterrows():
        price, iv = _model_iv(row, params)
        weight = float(row.get("vega", 1.0))
        residuals.append(math.sqrt(weight) * (iv - float(row["mid_iv"])))
    return np.asarray(residuals)


def _to_internal(params: np.ndarray) -> np.ndarray:
    params = np.asarray(params, dtype=float)
    internal = np.empty_like(params)
    for idx in POSITIVE_IDX:
        internal[idx] = math.log(max(params[idx], LOWER_BOUNDS[idx]))
    rho = float(np.clip(params[3], LOWER_BOUNDS[3] + 1e-6, UPPER_BOUNDS[3] - 1e-6))
    internal[3] = math.atanh(rho)
    return internal


def _from_internal(internal: np.ndarray) -> np.ndarray:
    internal = np.asarray(internal, dtype=float)
    params = np.empty_like(internal)
    for idx in POSITIVE_IDX:
        params[idx] = float(
            np.clip(math.exp(internal[idx]), LOWER_BOUNDS[idx], UPPER_BOUNDS[idx])
        )
    params[3] = float(np.clip(math.tanh(internal[3]), LOWER_BOUNDS[3], UPPER_BOUNDS[3]))
    return params


def _objective_internal(internal_vec: np.ndarray, surface: pd.DataFrame) -> np.ndarray:
    params_vec = _from_internal(internal_vec)
    return _objective(params_vec, surface)


def _params_tuple(params_dict: Dict[str, float]) -> Params:
    return (
        float(params_dict["kappa"]),
        float(params_dict["theta"]),
        float(params_dict["sigma"]),
        float(params_dict["rho"]),
        float(params_dict["v0"]),
    )


def apply_model(surface: pd.DataFrame, params_dict: Dict[str, float]) -> pd.DataFrame:
    params = _params_tuple(params_dict)
    out = surface.copy()
    prices = []
    ivs = []
    for _, row in out.iterrows():
        price, iv = _model_iv(row, params)
        prices.append(price)
        ivs.append(iv)
    out["model_price"] = prices
    out["model_iv"] = ivs
    out["iv_error_vol"] = out["model_iv"] - out["mid_iv"]
    out["iv_error_bps"] = out["iv_error_vol"] * 1e4
    out["price_error_ticks"] = (out["model_price"] - out["mid_price"]) / TICK_SIZE
    return out


def calibrate(surface: pd.DataFrame, config: CalibrationConfig) -> Dict[str, object]:
    surface = surface.copy()
    surface["vega"] = surface["vega"].where(surface["vega"] > 0, 1.0)

    x0 = np.array([1.0, 0.05, 0.5, -0.5, 0.04])
    internal0 = _to_internal(x0)
    result = least_squares(
        _objective_internal,
        x0=internal0,
        args=(surface,),
        max_nfev=config.max_evals,
        method="trf",
        diff_step=1e-2,
    )
    params_vec = _from_internal(result.x)
    params = tuple(params_vec.tolist())

    surface = apply_model(
        surface,
        {
            "kappa": params[0],
            "theta": params[1],
            "sigma": params[2],
            "rho": params[3],
            "v0": params[4],
        },
    )
    insample_metrics = compute_insample_metrics(surface)

    return {
        "params": {
            "kappa": params[0],
            "theta": params[1],
            "sigma": params[2],
            "rho": params[3],
            "v0": params[4],
        },
        "surface": surface,
        **insample_metrics,
        "success": bool(result.success),
        "nit": int(result.nfev),
    }


def bootstrap_confidence_intervals(
    surface: pd.DataFrame, params: Dict[str, float], config: CalibrationConfig
) -> Dict[str, Tuple[float, float]]:
    rng = random.Random(config.rng_seed)
    keys = ["kappa", "theta", "sigma", "rho", "v0"]
    samples = {key: [] for key in keys}
    n = len(surface)
    boot_iters = (
        config.bootstrap_samples
        if not config.fast
        else max(32, config.bootstrap_samples // 3)
    )
    for _ in range(boot_iters):
        idx = [rng.randrange(0, n) for _ in range(n)]
        boot = surface.iloc[idx].reset_index(drop=True)
        try:
            res = calibrate(
                boot,
                CalibrationConfig(
                    fast=True,
                    max_evals=80,
                    bootstrap_samples=0,
                    rng_seed=rng.randrange(1, 1_000_000),
                ),
            )
        except Exception:
            continue
        for key in keys:
            samples[key].append(float(res["params"][key]))
    ci = {}
    for key in keys:
        arr = samples[key]
        if not arr:
            ci[key] = (params[key], params[key])
        else:
            lo, hi = np.percentile(arr, [5, 95])
            ci[key] = (float(lo), float(hi))
    return ci


def write_tables(out_csv: Path, surface: pd.DataFrame) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "symbol",
        "trade_date",
        "tenor_bucket",
        "moneyness",
        "ttm_years",
        "mid_price",
        "model_price",
        "mid_iv",
        "model_iv",
        "iv_error_bps",
        "price_error_ticks",
        "quotes",
    ]
    surface[cols].to_csv(out_csv, index=False)


def write_summary(out_json: Path, payload: Dict[str, object]) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n")


def plot_fit(
    surface: pd.DataFrame,
    params: Dict[str, float],
    metrics: Dict[str, float],
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for bucket, group in surface.groupby("tenor_bucket", observed=True):
        axes[0].plot(
            group["moneyness"], group["mid_iv"], "o-", label=f"{bucket} market"
        )
        axes[0].plot(
            group["moneyness"], group["model_iv"], "--", label=f"{bucket} model"
        )
    axes[0].set_xlabel("Moneyness")
    axes[0].set_ylabel("Implied vol")
    axes[0].grid(True, ls=":", alpha=0.5)

    axes[1].plot(
        surface["moneyness"], surface["price_error_ticks"], "s", color="#d62728"
    )
    axes[1].axhline(0.0, color="black", linewidth=1)
    axes[1].set_xlabel("Moneyness")
    axes[1].set_ylabel("Price error (ticks)")
    axes[1].grid(True, ls=":", alpha=0.5)

    vol_rmse_pts = metrics["iv_rmse_volpts_vega_wt"] * 100.0
    price_rmse_ticks = metrics["price_rmse_ticks"]
    fig.suptitle(
        f"Heston fit | vega-wtd RMSE={vol_rmse_pts:.2f} vol pts, price RMSE={price_rmse_ticks:.2f} ticks"
    )
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles[::2], labels[::2], fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def record_manifest(
    out_json: Path, summary: Dict[str, object], surface_csv: Path, figure: Path
) -> None:
    payload = {
        "summary": str(out_json),
        "surface_csv": str(surface_csv),
        "figure": str(figure),
        "params": summary["params"],
        "iv_rmse_volpts_vega_wt": summary["iv_rmse_volpts_vega_wt"],
        "iv_mae_volpts_vega_wt": summary["iv_mae_volpts_vega_wt"],
        "iv_p90_bps": summary["iv_p90_bps"],
        "price_rmse_ticks": summary["price_rmse_ticks"],
        "iv_mae_bps": summary.get("iv_mae_bps"),
    }
    update_run("wrds_heston", payload, append=True)

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

from .asof_checks import assert_quote_date_matches
from .bs_utils import bs_call, bs_delta_call, bs_vega, implied_vol_from_price

Params = Tuple[float, float, float, float, float]  # kappa, theta, sigma, rho, v0
TICK_SIZE = 0.05
# Tighter, SPX-like bounds to keep the optimizer away from numerically toxic regions
# while still covering stressed regimes.
LOWER_BOUNDS = np.array([0.15, 0.0005, 0.05, -0.999, 0.0005], dtype=float)
UPPER_BOUNDS = np.array([6.0, 0.20, 1.50, 0.10, 0.20], dtype=float)
POSITIVE_IDX = [0, 1, 2, 4]

# 32-point Gauss–Laguerre (matches the C++ analytic implementation)
GL32_X = np.array(
    [
        0.044489365833267285,
        0.23452610951961964,
        0.5768846293018867,
        1.072448753817818,
        1.7224087764446454,
        2.5283367064257942,
        3.492213273021994,
        4.616456769749767,
        5.903958504174244,
        7.358126733186241,
        8.982940924212595,
        10.783018632539973,
        12.763697986742725,
        14.931139755522558,
        17.292454336715313,
        19.855860940336054,
        22.630889013196775,
        25.628636022459247,
        28.862101816323474,
        32.346629153964734,
        36.10049480575197,
        40.14571977153944,
        44.50920799575494,
        49.22439498730864,
        54.33372133339691,
        59.89250916213402,
        65.97537728793505,
        72.68762809066271,
        80.18744697791352,
        88.7353404178924,
        98.82954286828397,
        111.7513980979377,
    ],
    dtype=np.float64,
)
GL32_W = np.array(
    [
        0.10921834195241631,
        0.21044310793883672,
        0.23521322966983194,
        0.1959033359728629,
        0.12998378628606097,
        0.07057862386571173,
        0.03176091250917226,
        0.011918214834837557,
        0.003738816294611212,
        0.0009808033066148732,
        0.00021486491880134604,
        3.9203419679876094e-05,
        5.934541612868126e-06,
        7.416404578666935e-07,
        7.604567879120183e-08,
        6.350602226625271e-09,
        4.2813829710405056e-10,
        2.305899491891127e-11,
        9.79937928872617e-13,
        3.237801657729003e-14,
        8.171823443420105e-16,
        1.5421338333936845e-17,
        2.119792290163458e-19,
        2.054429673787832e-21,
        1.3469825866373068e-23,
        5.661294130396917e-26,
        1.4185605454629279e-28,
        1.91337549445389e-31,
        1.1922487600980343e-34,
        2.6715112192398583e-38,
        1.3386169421063085e-42,
        4.5105361938984096e-48,
    ],
    dtype=np.float64,
)


def _heston_cf(u: complex, T: float, params: Params, r: float, q: float, log_spot: float) -> complex:
    """Risk-neutral characteristic function φ(u).

    Mirrors quant::heston::characteristic_function (C++) to stay numerically consistent
    with the analytic pricer and to minimise branch cut surprises.
    """
    kappa, theta, sigma, rho, v0 = params
    iu = 1j * u
    sigma2 = sigma * sigma
    d = np.sqrt((rho * sigma * iu - kappa) ** 2 + sigma2 * (1j * u + u * u))
    denom = (kappa - rho * sigma * iu + d)
    denom_safe = np.where(np.abs(denom) < 1e-14, denom + 1e-14, denom)
    g = (kappa - rho * sigma * iu - d) / denom_safe
    exp_dT = np.exp(-d * T)
    one_minus_g = 1.0 - g
    one_minus_g_exp = 1.0 - g * exp_dT
    # Stabilise logs near zero to avoid NaNs
    log_term = np.log(one_minus_g_exp / np.where(np.abs(one_minus_g) < 1e-14, one_minus_g + 1e-14, one_minus_g))
    C = iu * (log_spot + (r - q) * T) + (kappa * theta / sigma2) * (
        (kappa - rho * sigma * iu - d) * T - 2.0 * log_term
    )
    D = ((kappa - rho * sigma * iu - d) / sigma2) * ((1.0 - exp_dT) / one_minus_g_exp)
    return np.exp(C + D * v0)


def heston_call_price(
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Params,
    n_points: int = 32,
    phi_max: float | None = None,
) -> float:
    if T <= 0.0:
        return max(spot - strike, 0.0)

    log_spot = math.log(spot)
    log_strike = math.log(strike)

    def _p_j(j: int) -> float:
        phi_minus_i = _heston_cf(-1j, T, params, rate, div, log_spot)
        acc = 0.0
        for x, w in zip(GL32_X, GL32_W):
            if w == 0.0:
                continue
            u = x  # Laguerre node
            if j == 1:
                phi = _heston_cf(u - 1j, T, params, rate, div, log_spot) / (phi_minus_i + 1e-16)
            else:
                phi = _heston_cf(u, T, params, rate, div, log_spot)
            integrand = cmath.exp(-1j * u * log_strike) * phi / (1j * u)
            # Transform ∫ f(u) du to Gauss–Laguerre: ∫ e^{-x} [e^{x} f(x)] dx
            acc += w * math.exp(x) * integrand.real
        return 0.5 + acc / math.pi

    import cmath

    p1 = _p_j(1)
    p2 = _p_j(2)

    df_r = math.exp(-rate * T)
    df_q = math.exp(-div * T)
    intrinsic = max(0.0, spot * df_q - strike * df_r)
    price = spot * df_q * p1 - strike * df_r * p2
    # Enforce no-arbitrage bounds to keep the implied-vol solver well-behaved.
    upper = spot * df_q
    price = float(min(max(price, intrinsic + 1e-10), upper))
    return price


def _model_iv(row: pd.Series, params: Params) -> Tuple[float, float]:
    T = float(row["ttm_years"])
    spot = float(row["spot"])
    strike = float(row["strike"])
    rate = float(row["rate"])
    div = float(row["dividend"])

    price = heston_call_price(spot=spot, strike=strike, rate=rate, div=div, T=T, params=params)
    intrinsic = max(0.0, spot * math.exp(-div * T) - strike * math.exp(-rate * T))
    upper = spot * math.exp(-div * T)
    price = float(min(max(price, intrinsic + 1e-10), upper))

    iv = implied_vol_from_price(
        price,
        spot,
        strike,
        rate,
        div,
        T,
        option="call",
    )
    if not math.isfinite(iv) or iv <= 0.0:
        iv = float("nan")
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


def _moneyness_taper(surface: pd.DataFrame) -> np.ndarray:
    m = np.asarray(surface.get("moneyness", 1.0), dtype=np.float64)
    # Softly down-weight wings beyond 1.2 or below 0.8 to stop edge quotes dominating.
    dist = np.abs(m - 1.0)
    taper = np.ones_like(dist)
    mask = dist > 0.2
    taper[mask] = np.exp(-6.0 * (dist[mask] - 0.2))  # ~0.37 weight at m=1.25
    return taper


def _vega_quote_weights(surface: pd.DataFrame, default: float = 1.0) -> np.ndarray:
    """Positive weights combining liquidity (quotes), sensitivity (vega), and wing taper."""
    vega = surface.get("vega", default)
    quotes = surface.get("quotes", 1.0)
    taper = _moneyness_taper(surface)
    weights = np.asarray(vega, dtype=np.float64) * np.asarray(quotes, dtype=np.float64) * taper
    return _positive_weights(weights, default=default)


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
    weights_all = _vega_quote_weights(surface)
    iv_errors = (surface["model_iv"] - surface["mid_iv"]).to_numpy(np.float64)
    iv_mask = np.isfinite(iv_errors) & np.isfinite(weights_all)
    if not iv_mask.any():
        return {
            "iv_rmse_volpts_vega_wt": float("nan"),
            "iv_mae_volpts_vega_wt": float("nan"),
            "iv_p90_bps": float("nan"),
            "price_rmse_ticks": float("nan"),
        }
    iv_errors = iv_errors[iv_mask]
    iv_weights = weights_all[iv_mask]
    abs_iv = np.abs(iv_errors)
    iv_rmse_volpts_vega_wt = float(
        np.sqrt(np.average(np.square(iv_errors), weights=iv_weights))
    )
    iv_mae_volpts_vega_wt = float(np.average(abs_iv, weights=iv_weights))
    iv_p90_bps = _weighted_percentile(abs_iv * 1e4, iv_weights, 0.9)

    price_errors = surface["price_error_ticks"].to_numpy(np.float64)
    price_mask = np.isfinite(price_errors) & np.isfinite(weights_all)
    price_errors = price_errors[price_mask]
    price_weights = weights_all[price_mask]
    price_rmse_ticks = (
        float(np.sqrt(np.average(np.square(price_errors), weights=price_weights)))
        if price_errors.size
        else float("nan")
    )
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
    weights = _vega_quote_weights(surface, default=1.0)
    iv_error_bps = surface["iv_error_bps"].to_numpy(np.float64)
    mask = np.isfinite(iv_error_bps)
    if not mask.any():
        return {"iv_mae_bps": float("nan")}
    weights = weights[mask]
    iv_error_bps = iv_error_bps[mask]
    iv_mae_bps = float(np.average(np.abs(iv_error_bps), weights=weights))
    return {
        "iv_mae_bps": iv_mae_bps,
    }


def _objective(params_vec: np.ndarray, surface: pd.DataFrame) -> np.ndarray:
    kappa, theta, sigma, rho, v0 = params_vec
    params: Params = (
        max(kappa, LOWER_BOUNDS[0]),
        max(theta, LOWER_BOUNDS[1]),
        max(sigma, LOWER_BOUNDS[2]),
        np.clip(rho, LOWER_BOUNDS[3], UPPER_BOUNDS[3]),
        max(v0, LOWER_BOUNDS[4]),
    )
    residuals = []
    penalty = 10.0  # vol points; large enough to steer solver away from bad regions
    for _, row in surface.iterrows():
        price, iv = _model_iv(row, params)
        weight = float(row.get("vega", 1.0)) * float(max(row.get("quotes", 1.0), 1.0))
        target = float(row["mid_iv"])
        if not math.isfinite(iv) or iv <= 0.0 or iv > 5.0:
            residuals.append(math.sqrt(weight) * penalty)
        else:
            residuals.append(math.sqrt(weight) * (iv - target))
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
    out["weight"] = _vega_quote_weights(out, default=1.0)
    return out


def calibrate(surface: pd.DataFrame, config: CalibrationConfig) -> Dict[str, object]:
    surface = surface.copy()
    assert_quote_date_matches(surface, context="calibration")
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
    if config.fast:
        boot_iters = min(12, max(4, config.bootstrap_samples // 4))
    else:
        boot_iters = config.bootstrap_samples
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
        "vega",
        "mid_price",
        "model_price",
        "mid_iv",
        "model_iv",
        "iv_error_bps",
        "price_error_ticks",
        "quotes",
        "weight",
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
        "trade_date": summary.get("trade_date"),
        "next_trade_date": summary.get("next_trade_date"),
        "params": summary["params"],
        "iv_rmse_volpts_vega_wt": summary["iv_rmse_volpts_vega_wt"],
        "iv_mae_volpts_vega_wt": summary["iv_mae_volpts_vega_wt"],
        "iv_p90_bps": summary["iv_p90_bps"],
        "price_rmse_ticks": summary["price_rmse_ticks"],
        "iv_mae_bps": summary.get("iv_mae_bps"),
    }
    update_run("wrds_heston", payload, append=True)

#!/usr/bin/env python3
"""Heston calibration utilities for WRDS aggregate surfaces."""
from __future__ import annotations

import dataclasses
import json
import math
import random
from functools import lru_cache
from pathlib import Path
from typing import Dict, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import update_run
from scipy.optimize import least_squares
from scipy.special import roots_laguerre

from .asof_checks import assert_quote_date_matches
from .bs_utils import implied_vol_from_price

Params = Tuple[float, float, float, float, float]  # kappa, theta, sigma, rho, v0
TICK_SIZE = 0.05
# Physical-domain bounds deliberately cover calm and crisis equity-index regimes.
# They are solver guards, not economic priors or a way to clip fitted output.
LOWER_BOUNDS = np.array([0.01, 1.0e-5, 0.01, -0.999, 1.0e-5], dtype=float)
UPPER_BOUNDS = np.array([15.0, 1.00, 5.00, 0.999, 1.00], dtype=float)
PARAMETER_NAMES = ("kappa", "theta", "sigma", "rho", "v0")
BOUNDARY_MARGIN_FRACTION = 1.0e-3
DEFAULT_QUADRATURE_POINTS = 96
DEFAULT_LAGUERRE_SCALE = 0.33
REFERENCE_QUADRATURE_POINTS = 128
REFERENCE_LAGUERRE_SCALE = 0.50
CALIBRATION_STARTS: Tuple[Params, ...] = (
    (1.0, 0.04, 0.50, -0.70, 0.04),
    (0.5, 0.25, 1.50, -0.85, 0.25),
    (3.0, 0.02, 0.30, -0.30, 0.02),
)


def _heston_cf(
    u: complex,
    T: float,
    params: Params,
    r: float,
    q: float,
    log_spot: float,
) -> complex:
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
    stable_one_minus_g = np.where(
        np.abs(one_minus_g) < 1e-14,
        one_minus_g + 1e-14,
        one_minus_g,
    )
    log_term = np.log(one_minus_g_exp / stable_one_minus_g)
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
    n_points: int = DEFAULT_QUADRATURE_POINTS,
    phi_max: float | None = None,
    laguerre_scale: float = DEFAULT_LAGUERRE_SCALE,
) -> float:
    """Return the un-clipped analytic Heston call price.

    ``n_points`` and ``laguerre_scale`` are genuine numerical controls.  The
    previous implementation exposed ``n_points`` but silently used a fixed
    32-point rule, then clipped invalid prices into no-arbitrage bounds.  That
    combination hid quadrature failures from calibration and Greeks.
    """
    if T <= 0.0:
        return max(spot - strike, 0.0)
    if n_points < 16:
        raise ValueError("n_points must be at least 16")
    if not math.isfinite(laguerre_scale) or laguerre_scale <= 0.0:
        raise ValueError("laguerre_scale must be positive and finite")
    if phi_max is not None:
        raise ValueError(
            "phi_max was historically ignored; use n_points and laguerre_scale"
        )

    log_spot = math.log(spot)
    log_strike = math.log(strike)
    nodes, transformed_weights = _scaled_laguerre_rule(
        n_points, laguerre_scale
    )

    def _p_j(j: int) -> float:
        phi_minus_i = _heston_cf(-1j, T, params, rate, div, log_spot)
        terms = []
        for u, transformed_weight in zip(nodes, transformed_weights):
            if j == 1:
                phi = _heston_cf(u - 1j, T, params, rate, div, log_spot) / (phi_minus_i + 1e-16)
            else:
                phi = _heston_cf(u, T, params, rate, div, log_spot)
            integrand = cmath.exp(-1j * u * log_strike) * phi / (1j * u)
            terms.append(float(transformed_weight) * integrand.real)
        return 0.5 + math.fsum(terms) / math.pi

    import cmath

    p1 = _p_j(1)
    p2 = _p_j(2)

    df_r = math.exp(-rate * T)
    df_q = math.exp(-div * T)
    price = spot * df_q * p1 - strike * df_r * p2
    return float(price)


@lru_cache(maxsize=16)
def _scaled_laguerre_rule(
    n_points: int, laguerre_scale: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Return nodes/weights for ``u=x/scale`` without overflow-prone products."""
    raw_nodes, raw_weights = roots_laguerre(int(n_points))
    nodes = np.asarray(raw_nodes / laguerre_scale, dtype=np.float64)
    log_weights = np.full_like(raw_weights, -np.inf, dtype=np.float64)
    positive = raw_weights > 0.0
    log_weights[positive] = np.log(raw_weights[positive])
    transformed = np.exp(log_weights + raw_nodes) / laguerre_scale
    nodes.setflags(write=False)
    transformed.setflags(write=False)
    return nodes, transformed


def _model_iv(
    row: pd.Series,
    params: Params,
    *,
    n_points: int = DEFAULT_QUADRATURE_POINTS,
    laguerre_scale: float = DEFAULT_LAGUERRE_SCALE,
) -> Tuple[float, float]:
    T = float(row["ttm_years"])
    spot = float(row["spot"])
    strike = float(row["strike"])
    rate = float(row["rate"])
    div = float(row["dividend"])

    price = heston_call_price(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=params,
        n_points=n_points,
        laguerre_scale=laguerre_scale,
    )
    intrinsic = max(0.0, spot * math.exp(-div * T) - strike * math.exp(-rate * T))
    upper = spot * math.exp(-div * T)
    price_tolerance = 1e-10 * max(1.0, spot, strike)
    if (
        not math.isfinite(price)
        or price < intrinsic - price_tolerance
        or price > upper + price_tolerance
    ):
        return price, float("nan")

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
    quadrature_points: int = DEFAULT_QUADRATURE_POINTS
    laguerre_scale: float = DEFAULT_LAGUERRE_SCALE
    multistart: bool = True


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


def _objective(
    params_vec: np.ndarray,
    surface: pd.DataFrame,
    n_points: int = DEFAULT_QUADRATURE_POINTS,
    laguerre_scale: float = DEFAULT_LAGUERRE_SCALE,
) -> np.ndarray:
    params: Params = (
        float(params_vec[0]),
        float(params_vec[1]),
        float(params_vec[2]),
        float(params_vec[3]),
        float(params_vec[4]),
    )
    residuals = []
    penalty = 10.0  # vol points; large enough to steer solver away from bad regions
    for _, row in surface.iterrows():
        price, iv = _model_iv(
            row,
            params,
            n_points=n_points,
            laguerre_scale=laguerre_scale,
        )
        weight = float(row.get("vega", 1.0)) * float(max(row.get("quotes", 1.0), 1.0))
        target = float(row["mid_iv"])
        if not math.isfinite(iv) or iv <= 0.0 or iv > 5.0:
            residuals.append(math.sqrt(weight) * penalty)
        else:
            residuals.append(math.sqrt(weight) * (iv - target))
    return np.asarray(residuals)


def _params_tuple(params_dict: Dict[str, float]) -> Params:
    return (
        float(params_dict["kappa"]),
        float(params_dict["theta"]),
        float(params_dict["sigma"]),
        float(params_dict["rho"]),
        float(params_dict["v0"]),
    )


def _bound_tolerance(idx: int) -> float:
    span = float(UPPER_BOUNDS[idx] - LOWER_BOUNDS[idx])
    return max(1e-12, 1e-9 * span)


def calibration_diagnostics(
    result,
    params_vec: np.ndarray,
    *,
    start_diagnostics: Sequence[Dict[str, object]] | None = None,
    selected_start_index: int = 0,
) -> Dict[str, object]:
    params_vec = np.asarray(params_vec, dtype=float)
    active_mask = np.asarray(
        getattr(result, "active_mask", np.zeros_like(params_vec)), dtype=int
    )
    lower_hits: Dict[str, bool] = {}
    upper_hits: Dict[str, bool] = {}
    normalized_boundary_distance: Dict[str, float] = {}
    active_params: list[str] = []
    for idx, name in enumerate(PARAMETER_NAMES):
        tol = _bound_tolerance(idx)
        span = float(UPPER_BOUNDS[idx] - LOWER_BOUNDS[idx])
        normalized = float((params_vec[idx] - LOWER_BOUNDS[idx]) / span)
        distance = min(normalized, 1.0 - normalized)
        normalized_boundary_distance[name] = distance
        lower_hit = bool(
            active_mask[idx] < 0
            or abs(params_vec[idx] - LOWER_BOUNDS[idx]) <= tol
            or normalized <= BOUNDARY_MARGIN_FRACTION
        )
        upper_hit = bool(
            active_mask[idx] > 0
            or abs(params_vec[idx] - UPPER_BOUNDS[idx]) <= tol
            or normalized >= 1.0 - BOUNDARY_MARGIN_FRACTION
        )
        lower_hits[name] = lower_hit
        upper_hits[name] = upper_hit
        if lower_hit or upper_hit:
            active_params.append(name)

    active_count = len(active_params)
    success = bool(getattr(result, "success", False))
    if success and active_count == 0:
        promotion_status = "eligible"
    elif success and active_count > 0:
        promotion_status = "boundary_saturated"
    elif not success and active_count > 0:
        promotion_status = "boundary_saturated_nonconverged"
    else:
        promotion_status = "nonconverged"

    njev = getattr(result, "njev", None)
    return {
        "success": success,
        "status": int(getattr(result, "status", 0)),
        "nfev": int(getattr(result, "nfev", 0)),
        "njev": None if njev is None else int(njev),
        "cost": float(getattr(result, "cost", float("nan"))),
        "optimality": float(getattr(result, "optimality", float("nan"))),
        "message": str(getattr(result, "message", "")),
        "active_bound_count": active_count,
        "active_bound_params": active_params,
        "optimizer_active_mask": {
            name: int(active_mask[idx]) for idx, name in enumerate(PARAMETER_NAMES)
        },
        "boundary_margin_fraction": BOUNDARY_MARGIN_FRACTION,
        "normalized_boundary_distance": normalized_boundary_distance,
        "minimum_normalized_boundary_distance": min(
            normalized_boundary_distance.values()
        ),
        "lower_bound_hits": lower_hits,
        "upper_bound_hits": upper_hits,
        "multistart_count": len(start_diagnostics or ()),
        "selected_start_index": int(selected_start_index),
        "start_diagnostics": list(start_diagnostics or ()),
        "promotion_eligible": bool(success and active_count == 0),
        "promotion_status": promotion_status,
        "ineligible_for_superiority_or_risk_promotion": bool(
            (not success) or active_count > 0
        ),
    }


def apply_model(
    surface: pd.DataFrame,
    params_dict: Dict[str, float],
    *,
    n_points: int = DEFAULT_QUADRATURE_POINTS,
    laguerre_scale: float = DEFAULT_LAGUERRE_SCALE,
) -> pd.DataFrame:
    params = _params_tuple(params_dict)
    out = surface.copy()
    prices = []
    ivs = []
    for _, row in out.iterrows():
        price, iv = _model_iv(
            row,
            params,
            n_points=n_points,
            laguerre_scale=laguerre_scale,
        )
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

    if config.quadrature_points < 16:
        raise ValueError("quadrature_points must be at least 16")
    if not math.isfinite(config.laguerre_scale) or config.laguerre_scale <= 0.0:
        raise ValueError("laguerre_scale must be positive and finite")

    starts = (
        CALIBRATION_STARTS
        if config.multistart and not config.fast
        else CALIBRATION_STARTS[:1]
    )
    results = []
    start_diagnostics: list[Dict[str, object]] = []
    for start_index, start in enumerate(starts):
        result = least_squares(
            _objective,
            x0=np.asarray(start, dtype=float),
            bounds=(LOWER_BOUNDS, UPPER_BOUNDS),
            args=(surface, config.quadrature_points, config.laguerre_scale),
            max_nfev=config.max_evals,
            method="trf",
            diff_step=1e-2,
            x_scale="jac",
        )
        results.append(result)
        start_diagnostics.append(
            {
                "start_index": start_index,
                "success": bool(result.success),
                "status": int(result.status),
                "nfev": int(result.nfev),
                "cost": float(result.cost),
                "optimality": float(result.optimality),
            }
        )
    finite_results = [
        (idx, result)
        for idx, result in enumerate(results)
        if math.isfinite(float(result.cost))
    ]
    if not finite_results:
        raise RuntimeError("all deterministic Heston calibration starts failed")
    selected_start_index, result = min(
        finite_results, key=lambda item: (float(item[1].cost), item[0])
    )
    params_vec = np.asarray(result.x, dtype=float)
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
        n_points=config.quadrature_points,
        laguerre_scale=config.laguerre_scale,
    )
    insample_metrics = compute_insample_metrics(surface)
    diagnostics = calibration_diagnostics(
        result,
        params_vec,
        start_diagnostics=start_diagnostics,
        selected_start_index=selected_start_index,
    )
    diagnostics.update(
        {
            "quadrature_points": int(config.quadrature_points),
            "laguerre_scale": float(config.laguerre_scale),
            "price_output_clipped": False,
            "solver_coordinates": "physical_bounded",
        }
    )

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
        "diagnostics": diagnostics,
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
                    quadrature_points=config.quadrature_points,
                    laguerre_scale=config.laguerre_scale,
                    multistart=False,
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

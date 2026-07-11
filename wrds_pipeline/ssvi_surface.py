#!/usr/bin/env python3
"""Arbitrage-aware power-law SSVI benchmark for aggregate option surfaces.

The surface follows Gatheral-Jacquier SSVI with a monotone piecewise-linear ATM
total-variance curve.  Smooth parameter transforms enforce positivity,
monotonicity, ``|rho| < 1``, and sufficient SSVI butterfly conditions on the
declared maturity domain.  Numerical density, calendar, and call-price checks
remain independent promotion gates rather than optimization penalties.
"""
from __future__ import annotations

import dataclasses
import math
from typing import Dict, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.special import expit

from .asof_checks import assert_quote_date_matches
from .bs_utils import bs_call
from .calibrate_heston import (
    TICK_SIZE,
    _vega_quote_weights,
    compute_insample_metrics,
)

KNOT_YEARS = np.asarray([30.0, 60.0, 90.0, 182.0, 365.0]) / 365.0
KNOT_BUCKETS = ("30d", "60d", "90d", "6m", "1y")
PARAMETER_COUNT = len(KNOT_YEARS) + 3
VALIDATION_T_MIN = 20.0 / 365.0
VALIDATION_T_MAX = 400.0 / 365.0
VALIDATION_K_MIN = -1.5
VALIDATION_K_MAX = 1.5
ARBITRAGE_MARGIN = 0.98
RHO_LIMIT = 0.999
GAMMA_MIN = 0.01
GAMMA_MAX = 0.99
THETA_INCREMENT_MIN = 1e-8
THETA_INCREMENT_MAX = 2.0


@dataclasses.dataclass(frozen=True)
class SsviParameters:
    theta_knots: Tuple[float, float, float, float, float]
    rho: float
    eta: float
    gamma: float

    def as_dict(self) -> Dict[str, object]:
        return {
            "theta_knots": list(self.theta_knots),
            "rho": self.rho,
            "eta": self.eta,
            "gamma": self.gamma,
        }


@dataclasses.dataclass(frozen=True)
class SsviCalibrationConfig:
    fast: bool = False
    max_evals: int = 500
    multistart: bool = True
    validation_t_min: float = VALIDATION_T_MIN
    validation_t_max: float = VALIDATION_T_MAX
    validation_k_min: float = VALIDATION_K_MIN
    validation_k_max: float = VALIDATION_K_MAX
    maturity_grid_size: int = 81
    log_moneyness_grid_size: int = 401


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        inverse = math.exp(-value)
        return 1.0 / (1.0 + inverse)
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def _logit(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        raise ValueError("logit input must be strictly between zero and one")
    return math.log(probability / (1.0 - probability))


def atm_total_variance(
    maturity: float | np.ndarray,
    theta_knots: Sequence[float],
) -> float | np.ndarray:
    """Monotone interpolation with theta(0)=0 and positive final extrapolation."""
    theta = np.asarray(theta_knots, dtype=np.float64)
    if theta.shape != KNOT_YEARS.shape:
        raise ValueError(f"theta_knots must contain {len(KNOT_YEARS)} values")
    if not np.isfinite(theta).all() or np.any(theta <= 0.0):
        raise ValueError("theta_knots must be positive and finite")
    if np.any(np.diff(theta) <= 0.0):
        raise ValueError("theta_knots must be strictly increasing")

    values = np.asarray(maturity, dtype=np.float64)
    result = np.interp(values, KNOT_YEARS, theta)
    left = values < KNOT_YEARS[0]
    result = np.where(left, theta[0] * values / KNOT_YEARS[0], result)
    final_slope = (theta[-1] - theta[-2]) / (KNOT_YEARS[-1] - KNOT_YEARS[-2])
    right = values > KNOT_YEARS[-1]
    result = np.where(
        right,
        theta[-1] + final_slope * (values - KNOT_YEARS[-1]),
        result,
    )
    if np.isscalar(maturity):
        return float(result)
    return result


def ssvi_total_variance(
    log_forward_moneyness: float | np.ndarray,
    theta: float | np.ndarray,
    params: SsviParameters,
) -> float | np.ndarray:
    k = np.asarray(log_forward_moneyness, dtype=np.float64)
    theta_array = np.asarray(theta, dtype=np.float64)
    phi = params.eta * np.power(theta_array, -params.gamma)
    shifted = phi * k + params.rho
    root = np.sqrt(shifted * shifted + 1.0 - params.rho * params.rho)
    result = 0.5 * theta_array * (1.0 + params.rho * phi * k + root)
    if np.isscalar(log_forward_moneyness) and np.isscalar(theta):
        return float(result)
    return result


def ssvi_total_variance_derivatives(
    log_forward_moneyness: float | np.ndarray,
    theta: float | np.ndarray,
    params: SsviParameters,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return w, first k derivative, and second k derivative analytically."""
    k = np.asarray(log_forward_moneyness, dtype=np.float64)
    theta_array = np.asarray(theta, dtype=np.float64)
    phi = params.eta * np.power(theta_array, -params.gamma)
    shifted = phi * k + params.rho
    one_minus_rho_sq = 1.0 - params.rho * params.rho
    root = np.sqrt(shifted * shifted + one_minus_rho_sq)
    variance = 0.5 * theta_array * (
        1.0 + params.rho * phi * k + root
    )
    first = 0.5 * theta_array * (
        params.rho * phi + phi * shifted / root
    )
    second = (
        0.5
        * theta_array
        * phi
        * phi
        * one_minus_rho_sq
        / np.power(root, 3.0)
    )
    return variance, first, second


def butterfly_density_factor(
    log_forward_moneyness: float | np.ndarray,
    theta: float | np.ndarray,
    params: SsviParameters,
) -> np.ndarray:
    """Return the Gatheral-Jacquier density factor g(k)."""
    k = np.asarray(log_forward_moneyness, dtype=np.float64)
    variance, first, second = ssvi_total_variance_derivatives(k, theta, params)
    return (
        np.square(1.0 - k * first / (2.0 * variance))
        - 0.25 * first * first * (1.0 / variance + 0.25)
        + 0.5 * second
    )


def _eta_cap(
    theta_knots: Sequence[float],
    rho: float,
    gamma: float,
    validation_t_min: float,
    validation_t_max: float,
) -> float:
    theta_endpoints = np.asarray(
        atm_total_variance(
            np.asarray([validation_t_min, validation_t_max]),
            theta_knots,
        ),
        dtype=np.float64,
    )
    if np.any(theta_endpoints <= 0.0):
        raise ValueError("validation-domain ATM variance must be positive")
    rho_factor = 1.0 + abs(rho)
    max_first = float(np.max(np.power(theta_endpoints, 1.0 - gamma)))
    max_second = float(np.max(np.power(theta_endpoints, 1.0 - 2.0 * gamma)))
    first_cap = 4.0 / (rho_factor * max_first)
    second_cap = math.sqrt(4.0 / (rho_factor * max_second))
    return ARBITRAGE_MARGIN * min(first_cap, second_cap)


def _from_raw(
    raw: np.ndarray,
    config: SsviCalibrationConfig,
) -> SsviParameters:
    raw = np.asarray(raw, dtype=np.float64)
    if raw.shape != (PARAMETER_COUNT,):
        raise ValueError(f"raw SSVI vector must have length {PARAMETER_COUNT}")
    increments = THETA_INCREMENT_MIN + (
        THETA_INCREMENT_MAX - THETA_INCREMENT_MIN
    ) * expit(raw[: len(KNOT_YEARS)])
    theta_knots = np.cumsum(increments)
    rho = RHO_LIMIT * math.tanh(float(raw[len(KNOT_YEARS)]))
    gamma_fraction = _sigmoid(float(raw[len(KNOT_YEARS) + 1]))
    gamma = GAMMA_MIN + (GAMMA_MAX - GAMMA_MIN) * gamma_fraction
    cap = _eta_cap(
        theta_knots,
        rho,
        gamma,
        config.validation_t_min,
        config.validation_t_max,
    )
    eta_fraction = _sigmoid(float(raw[len(KNOT_YEARS) + 2]))
    eta = cap * eta_fraction
    return SsviParameters(
        theta_knots=tuple(float(value) for value in theta_knots),  # type: ignore[arg-type]
        rho=rho,
        eta=eta,
        gamma=gamma,
    )


def _raw_start(
    theta_knots: Sequence[float],
    rho: float,
    gamma: float,
    eta_fraction: float,
) -> np.ndarray:
    theta = np.asarray(theta_knots, dtype=np.float64)
    increments = np.diff(np.concatenate(([0.0], theta)))
    if np.any(increments <= 0.0):
        raise ValueError("initial theta curve must be strictly increasing")
    raw = np.empty(PARAMETER_COUNT, dtype=np.float64)
    increment_fractions = (
        increments - THETA_INCREMENT_MIN
    ) / (THETA_INCREMENT_MAX - THETA_INCREMENT_MIN)
    increment_fractions = np.clip(increment_fractions, 1e-12, 1.0 - 1e-12)
    raw[: len(KNOT_YEARS)] = [
        _logit(float(fraction)) for fraction in increment_fractions
    ]
    raw[len(KNOT_YEARS)] = math.atanh(rho / RHO_LIMIT)
    gamma_fraction = (gamma - GAMMA_MIN) / (GAMMA_MAX - GAMMA_MIN)
    raw[len(KNOT_YEARS) + 1] = _logit(gamma_fraction)
    raw[len(KNOT_YEARS) + 2] = _logit(eta_fraction)
    return raw


def _initial_theta_curve(surface: pd.DataFrame) -> np.ndarray:
    target = []
    for bucket, knot in zip(KNOT_BUCKETS, KNOT_YEARS):
        group = surface[surface["tenor_bucket"].astype(str) == bucket]
        if group.empty:
            target.append(float(np.median(np.square(surface["mid_iv"]) * knot)))
            continue
        forward = group["spot"].to_numpy(np.float64) * np.exp(
            (group["rate"].to_numpy(np.float64) - group["dividend"].to_numpy(np.float64))
            * group["ttm_years"].to_numpy(np.float64)
        )
        log_moneyness = np.log(group["strike"].to_numpy(np.float64) / forward)
        near_atm = np.argsort(np.abs(log_moneyness))[: max(5, len(group) // 5)]
        sub = group.iloc[near_atm]
        weights = _vega_quote_weights(sub)
        total_variance = (
            np.square(sub["mid_iv"].to_numpy(np.float64))
            * sub["ttm_years"].to_numpy(np.float64)
        )
        target.append(float(np.average(total_variance, weights=weights)))
    theta = np.asarray(target, dtype=np.float64)
    theta = np.maximum.accumulate(np.maximum(theta, 1e-6))
    minimum_increment = 1e-6
    for idx in range(1, len(theta)):
        theta[idx] = max(theta[idx], theta[idx - 1] + minimum_increment)
    return theta


def _surface_arrays(surface: pd.DataFrame) -> Dict[str, np.ndarray]:
    maturity = surface["ttm_years"].to_numpy(np.float64)
    spot = surface["spot"].to_numpy(np.float64)
    strike = surface["strike"].to_numpy(np.float64)
    rate = surface["rate"].to_numpy(np.float64)
    dividend = surface["dividend"].to_numpy(np.float64)
    forward = spot * np.exp((rate - dividend) * maturity)
    return {
        "maturity": maturity,
        "log_forward_moneyness": np.log(strike / forward),
        "target_iv": surface["mid_iv"].to_numpy(np.float64),
        "weight": (
            np.maximum(surface["vega"].to_numpy(np.float64), 1e-12)
            * np.maximum(surface["quotes"].to_numpy(np.float64), 1.0)
        ),
    }


def _model_iv_arrays(
    maturity: np.ndarray,
    log_forward_moneyness: np.ndarray,
    params: SsviParameters,
) -> np.ndarray:
    theta = np.asarray(atm_total_variance(maturity, params.theta_knots))
    total_variance = np.asarray(
        ssvi_total_variance(log_forward_moneyness, theta, params)
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.sqrt(total_variance / maturity)


def _objective(
    raw: np.ndarray,
    arrays: Dict[str, np.ndarray],
    config: SsviCalibrationConfig,
) -> np.ndarray:
    params = _from_raw(raw, config)
    model_iv = _model_iv_arrays(
        arrays["maturity"],
        arrays["log_forward_moneyness"],
        params,
    )
    residual = model_iv - arrays["target_iv"]
    invalid = ~np.isfinite(residual) | (model_iv <= 0.0) | (model_iv > 5.0)
    residual[invalid] = 10.0
    return np.sqrt(arrays["weight"]) * residual


def model_iv(
    *,
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    maturity: float,
    params: SsviParameters,
) -> float:
    if not all(
        math.isfinite(value)
        for value in (spot, strike, rate, dividend, maturity)
    ):
        raise ValueError("SSVI market inputs must be finite")
    if spot <= 0.0 or strike <= 0.0 or maturity <= 0.0:
        raise ValueError("spot, strike, and maturity must be positive")
    forward = spot * math.exp((rate - dividend) * maturity)
    k = math.log(strike / forward)
    theta = float(atm_total_variance(maturity, params.theta_knots))
    total_variance = float(ssvi_total_variance(k, theta, params))
    if not math.isfinite(total_variance) or total_variance <= 0.0:
        return float("nan")
    return math.sqrt(total_variance / maturity)


def apply_surface(surface: pd.DataFrame, params: SsviParameters) -> pd.DataFrame:
    out = surface.copy()
    arrays = _surface_arrays(out)
    model_ivs = _model_iv_arrays(
        arrays["maturity"],
        arrays["log_forward_moneyness"],
        params,
    )
    model_prices = []
    for row, volatility in zip(out.itertuples(index=False), model_ivs):
        if not math.isfinite(float(volatility)) or volatility <= 0.0:
            model_prices.append(float("nan"))
            continue
        model_prices.append(
            bs_call(
                float(row.spot),
                float(row.strike),
                float(row.rate),
                float(row.dividend),
                float(volatility),
                float(row.ttm_years),
            )
        )
    out["model_iv"] = model_ivs
    out["model_price"] = model_prices
    out["iv_error_vol"] = out["model_iv"] - out["mid_iv"]
    out["iv_error_bps"] = out["iv_error_vol"] * 1e4
    out["price_error_ticks"] = (out["model_price"] - out["mid_price"]) / TICK_SIZE
    out["weight"] = _vega_quote_weights(out)
    return out


def summarize_oos(surface: pd.DataFrame) -> Dict[str, float | int]:
    weights = _vega_quote_weights(surface)
    iv_error = surface["iv_error_bps"].to_numpy(np.float64)
    price_error = surface["price_error_ticks"].to_numpy(np.float64)
    valid = np.isfinite(iv_error) & np.isfinite(price_error) & np.isfinite(weights)
    if not valid.any():
        return {
            "iv_mae_bps": float("nan"),
            "price_mae_ticks": float("nan"),
            "valid_rows": 0,
            "invalid_rows": int(len(surface)),
        }
    return {
        "iv_mae_bps": float(
            np.average(np.abs(iv_error[valid]), weights=weights[valid])
        ),
        "price_mae_ticks": float(
            np.average(np.abs(price_error[valid]), weights=weights[valid])
        ),
        "valid_rows": int(valid.sum()),
        "invalid_rows": int((~valid).sum()),
    }


def arbitrage_diagnostics(
    params: SsviParameters,
    config: SsviCalibrationConfig,
) -> Dict[str, object]:
    maturity_grid = np.linspace(
        config.validation_t_min,
        config.validation_t_max,
        config.maturity_grid_size,
    )
    k_grid = np.linspace(
        config.validation_k_min,
        config.validation_k_max,
        config.log_moneyness_grid_size,
    )
    theta_grid = np.asarray(
        atm_total_variance(maturity_grid, params.theta_knots),
        dtype=np.float64,
    )
    phi_grid = params.eta * np.power(theta_grid, -params.gamma)
    rho_factor = 1.0 + abs(params.rho)
    sufficient_wing_max = float(np.max(theta_grid * phi_grid * rho_factor))
    sufficient_curvature_max = float(
        np.max(theta_grid * phi_grid * phi_grid * rho_factor)
    )

    mesh_theta, mesh_k = np.meshgrid(theta_grid, k_grid, indexing="ij")
    total_variance = np.asarray(
        ssvi_total_variance(mesh_k, mesh_theta, params),
        dtype=np.float64,
    )
    calendar_differences = np.diff(total_variance, axis=0)
    density = butterfly_density_factor(mesh_k, mesh_theta, params)

    call_monotonicity_max_violation = 0.0
    call_convexity_min_slope_change = float("inf")
    strike_grid = 100.0 * np.exp(k_grid)
    for maturity, row_variance in zip(maturity_grid, total_variance):
        volatility = np.sqrt(row_variance / maturity)
        calls = np.asarray(
            [
                bs_call(100.0, float(strike), 0.0, 0.0, float(vol), maturity)
                for strike, vol in zip(strike_grid, volatility)
            ],
            dtype=np.float64,
        )
        call_monotonicity_max_violation = max(
            call_monotonicity_max_violation,
            float(np.max(np.diff(calls))),
        )
        slopes = np.diff(calls) / np.diff(strike_grid)
        call_convexity_min_slope_change = min(
            call_convexity_min_slope_change,
            float(np.min(np.diff(slopes))),
        )

    minimum_calendar_increment = float(np.min(calendar_differences))
    minimum_density_factor = float(np.min(density))
    minimum_total_variance = float(np.min(total_variance))
    analytic_pass = bool(
        sufficient_wing_max < 4.0
        and sufficient_curvature_max <= 4.0
        and 0.0 <= params.gamma <= 1.0
        and abs(params.rho) < 1.0
    )
    numerical_pass = bool(
        minimum_total_variance > 0.0
        and minimum_calendar_increment >= -1e-10
        and minimum_density_factor >= -1e-10
        and call_monotonicity_max_violation <= 1e-10
        and call_convexity_min_slope_change >= -1e-10
    )
    return {
        "status": "valid" if analytic_pass and numerical_pass else "invalid",
        "analytic_sufficient_conditions_pass": analytic_pass,
        "numerical_static_arbitrage_pass": numerical_pass,
        "sufficient_wing_max": sufficient_wing_max,
        "sufficient_wing_limit": 4.0,
        "sufficient_curvature_max": sufficient_curvature_max,
        "sufficient_curvature_limit": 4.0,
        "minimum_total_variance": minimum_total_variance,
        "minimum_calendar_increment": minimum_calendar_increment,
        "minimum_density_factor": minimum_density_factor,
        "call_monotonicity_max_violation": call_monotonicity_max_violation,
        "call_convexity_min_slope_change": call_convexity_min_slope_change,
        "maturity_domain_years": [
            config.validation_t_min,
            config.validation_t_max,
        ],
        "log_forward_moneyness_domain": [
            config.validation_k_min,
            config.validation_k_max,
        ],
        "maturity_grid_size": config.maturity_grid_size,
        "log_moneyness_grid_size": config.log_moneyness_grid_size,
    }


def calibrate(
    surface: pd.DataFrame,
    config: SsviCalibrationConfig | None = None,
) -> Dict[str, object]:
    config = config or SsviCalibrationConfig()
    if surface.empty:
        raise ValueError("cannot calibrate SSVI to an empty surface")
    if config.max_evals <= 0:
        raise ValueError("max_evals must be positive")
    if not 0.0 < config.validation_t_min < config.validation_t_max:
        raise ValueError("invalid SSVI validation maturity domain")
    if not config.validation_k_min < config.validation_k_max:
        raise ValueError("invalid SSVI validation moneyness domain")
    assert_quote_date_matches(surface, context="ssvi calibration")

    arrays = _surface_arrays(surface)
    initial_theta = _initial_theta_curve(surface)
    start_specs = (
        (1.00, -0.70, 0.50, 0.50),
        (0.80, -0.90, 0.25, 0.70),
        (1.20, -0.30, 0.75, 0.30),
    )
    if config.fast or not config.multistart:
        start_specs = start_specs[:1]

    results = []
    start_diagnostics = []
    for start_index, (scale, rho, gamma, eta_fraction) in enumerate(start_specs):
        raw_start = _raw_start(
            initial_theta * scale,
            rho,
            gamma,
            eta_fraction,
        )
        result = least_squares(
            _objective,
            x0=raw_start,
            args=(arrays, config),
            method="trf",
            max_nfev=config.max_evals,
            diff_step=1e-4,
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
        raise RuntimeError("all deterministic SSVI calibration starts failed")
    selected_start_index, selected = min(
        finite_results,
        key=lambda item: (float(item[1].cost), item[0]),
    )
    params = _from_raw(np.asarray(selected.x), config)
    modeled = apply_surface(surface, params)
    metrics = compute_insample_metrics(modeled)
    arbitrage = arbitrage_diagnostics(params, config)
    valid_rows = modeled[["model_iv", "model_price"]].replace(
        [np.inf, -np.inf], np.nan
    ).notnull().all(axis=1)
    promotion_eligible = bool(
        selected.success
        and valid_rows.all()
        and arbitrage["status"] == "valid"
    )
    diagnostics = {
        "success": bool(selected.success),
        "status": int(selected.status),
        "message": str(selected.message),
        "nfev": int(selected.nfev),
        "njev": int(selected.njev) if selected.njev is not None else None,
        "cost": float(selected.cost),
        "optimality": float(selected.optimality),
        "multistart_count": len(start_diagnostics),
        "selected_start_index": int(selected_start_index),
        "start_diagnostics": start_diagnostics,
        "valid_surface_rows": int(valid_rows.sum()),
        "invalid_surface_rows": int((~valid_rows).sum()),
        "parameterization": "power_law_ssvi_monotone_atm_curve",
        "objective": "vega_times_quote_weighted_iv_residual",
        "price_output_clipped": False,
        "arbitrage": arbitrage,
        "promotion_eligible": promotion_eligible,
        "promotion_status": "eligible" if promotion_eligible else "diagnostic_only",
    }
    return {
        "params": params,
        "surface": modeled,
        "metrics": metrics,
        "diagnostics": diagnostics,
    }

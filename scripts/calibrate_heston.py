#!/usr/bin/env python3
"""
Calibrate the Heston model to a single-day options surface in normalized schema.

The input CSV must follow `scripts/data/schema.md`. Outputs:
  * docs/artifacts/heston/params_<date>.json  - fitted parameters and metrics
  * docs/artifacts/heston/fit_<date>.png     - market vs model implied vol smiles
  * docs/artifacts/heston/fit_<date>.csv     - table backing the figure (strike, ttm, market_iv, model_iv, abs_error)

Usage:
  ./scripts/calibrate_heston.py --input data/normalized/spx_20240614.csv
  ./scripts/calibrate_heston.py --input data/samples/spx_20240614_sample.csv --fast
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run
from scipy.optimize import brentq, least_squares

Params = Tuple[float, float, float, float, float]  # kappa, theta, sigma, rho, v0


def black_scholes_call(
    spot: float, strike: float, r: float, q: float, sigma: float, T: float
) -> float:
    if T <= 0:
        return max(spot - strike, 0.0)
    sigma = max(1e-12, sigma)
    sqrtT = math.sqrt(T)
    d1 = (math.log(spot / strike) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    return spot * math.exp(-q * T) * nd1 - strike * math.exp(-r * T) * nd2


def black_scholes_put(
    spot: float, strike: float, r: float, q: float, sigma: float, T: float
) -> float:
    call_price = black_scholes_call(spot, strike, r, q, sigma, T)
    return call_price - spot * math.exp(-q * T) + strike * math.exp(-r * T)


def implied_vol_from_price(
    price: float,
    spot: float,
    strike: float,
    r: float,
    q: float,
    T: float,
    is_call: bool,
) -> float:
    if price <= 0.0 or T <= 0.0:
        return 0.0

    target = price

    def objective(vol: float) -> float:
        if is_call:
            return black_scholes_call(spot, strike, r, q, vol, T) - target
        return black_scholes_put(spot, strike, r, q, vol, T) - target

    try:
        return brentq(objective, 1e-6, 4.0, maxiter=100)
    except ValueError:
        # Fallback to approximate variance ratio if bracket fails
        intrinsic = (
            max(0.0, spot * math.exp(-q * T) - strike * math.exp(-r * T))
            if is_call
            else max(0.0, strike * math.exp(-r * T) - spot * math.exp(-q * T))
        )
        if target <= intrinsic + 1e-6:
            return 1e-6
        return 0.5


def _heston_characteristic(
    phi: float | np.ndarray,
    T: float,
    params: Params,
    r: float,
    q: float,
    log_spot: float,
    j: int,
) -> np.ndarray:
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
    denom = b - rho * sigma * i * phi - d
    g = (b - rho * sigma * i * phi + d) / (denom + 1e-16)
    exp_minus_dT = np.exp(-d * T)
    log_term = np.log((1.0 - g * exp_minus_dT) / (1.0 - g + 1e-16))
    C = (r - q) * i * phi * T + (a / (sigma * sigma)) * (
        (b - rho * sigma * i * phi + d) * T - 2.0 * log_term
    )
    D = ((b - rho * sigma * i * phi + d) / (sigma * sigma)) * (
        (1.0 - exp_minus_dT) / (1.0 - g * exp_minus_dT + 1e-16)
    )
    return np.exp(C + D * v0 + i * phi * log_spot)


def heston_call_price(
    spot: float,
    strike: float,
    r: float,
    q: float,
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
    cf1 = _heston_characteristic(phis, T, params, r, q, log_spot, 1)
    cf2 = _heston_characteristic(phis, T, params, r, q, log_spot, 2)
    exp_term = np.exp(-1j * phis * log_strike)
    denom = 1j * phis
    integrand1 = np.real(exp_term * cf1 / denom)
    integrand2 = np.real(exp_term * cf2 / denom)
    p1 = 0.5 + (1.0 / math.pi) * np.trapezoid(integrand1, phis)
    p2 = 0.5 + (1.0 / math.pi) * np.trapezoid(integrand2, phis)
    return spot * math.exp(-q * T) * p1 - strike * math.exp(-r * T) * p2


@dataclass
class CalibrationConfig:
    fast: bool = False
    max_evals: int = 200
    retries: int = 4
    seed: int = 7
    metric: str = "price"  # "price" or "vol"
    weight_mode: str = "iv"
    feller_warn: bool = False
    param_transform: str = "none"


def _sigmoid_forward(
    value: float | np.ndarray, lb: float, ub: float
) -> float | np.ndarray:
    return lb + (ub - lb) / (1.0 + np.exp(-value))


def _sigmoid_inverse(
    value: float | np.ndarray, lb: float, ub: float
) -> float | np.ndarray:
    clipped = np.clip((np.asarray(value) - lb) / (ub - lb + 1e-16), 1e-9, 1 - 1e-9)
    return np.log(clipped / (1.0 - clipped))


class ParameterTransform:
    def __init__(self, mode: str, lb: np.ndarray, ub: np.ndarray):
        if mode not in {"none", "exp", "sigmoid"}:
            raise ValueError(f"Unsupported param-transform '{mode}'")
        self.mode = mode
        self.lb = lb
        self.ub = ub

    def to_internal(self, params: np.ndarray) -> np.ndarray:
        params = np.asarray(params, dtype=float)
        if self.mode == "none":
            return params
        internal = np.empty_like(params)
        if self.mode == "exp":
            positive_idx = [0, 1, 2, 4]
            for idx in positive_idx:
                internal[idx] = math.log(max(params[idx], 1e-10))
            internal[3] = float(_sigmoid_inverse(params[3], self.lb[3], self.ub[3]))
            return internal
        # sigmoid
        for i in range(len(params)):
            internal[i] = float(_sigmoid_inverse(params[i], self.lb[i], self.ub[i]))
        return internal

    def from_internal(self, internal: np.ndarray) -> np.ndarray:
        internal = np.asarray(internal, dtype=float)
        if self.mode == "none":
            return internal
        params = np.empty_like(internal)
        if self.mode == "exp":
            positive_idx = [0, 1, 2, 4]
            for idx in positive_idx:
                params[idx] = float(
                    np.clip(np.exp(internal[idx]), self.lb[idx], self.ub[idx])
                )
            params[3] = float(_sigmoid_forward(internal[3], self.lb[3], self.ub[3]))
            return params
        # sigmoid
        for i in range(len(internal)):
            params[i] = float(_sigmoid_forward(internal[i], self.lb[i], self.ub[i]))
        return params

    def within_bounds(self, params: np.ndarray) -> bool:
        return bool(np.all(params >= self.lb) and np.all(params <= self.ub))


def _compute_weight_vector(
    df: pd.DataFrame, market_prices: np.ndarray, vegas: np.ndarray, mode: str
) -> np.ndarray:
    mode = mode.lower()
    if mode == "vega":
        return 1.0 / np.maximum(vegas, 1e-6)
    if mode == "bidask" and {"bid", "ask"}.issubset(df.columns):
        spread = df["ask"].to_numpy() - df["bid"].to_numpy()
        return 1.0 / np.maximum(spread, 1e-4)
    # default to implied-vol weighting
    iv = df["mid_iv"].to_numpy()
    return 1.0 / np.maximum(iv, 1e-3)


def _prepare_surface(df: pd.DataFrame, fast: bool) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    if df["date"].nunique() != 1:
        raise ValueError("Input surface must contain exactly one trade date")
    if fast:
        grouped = df.groupby("ttm_years", sort=True)
        keep_frames = []
        for _, frame in grouped:
            keep = frame.nsmallest(3, "strike")
            keep = pd.concat([keep, frame.nlargest(3, "strike")]).drop_duplicates()
            keep_frames.append(keep.head(6))
        df = pd.concat(keep_frames, ignore_index=True)
    return df


def _surface_market_prices(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    prices = []
    vegas = []
    for _, row in df.iterrows():
        S = float(row["spot"])
        K = float(row["strike"])
        r = float(row["r"])
        q = float(row["q"])
        T = float(row["ttm_years"])
        sigma = float(row["mid_iv"])
        if row["put_call"].lower() == "call":
            price = black_scholes_call(S, K, r, q, sigma, T)
        else:
            price = black_scholes_put(S, K, r, q, sigma, T)
        prices.append(price)
        sqrtT = math.sqrt(max(T, 1e-8))
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
        vega = (
            S
            * math.exp(-q * T)
            * math.sqrt(T)
            * (math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi))
        )
        vegas.append(max(vega, 1e-8))
    return np.array(prices), np.array(vegas)


def _model_prices(df: pd.DataFrame, params: Params, fast: bool) -> np.ndarray:
    n_points = 96 if fast else 256
    phi_max = 90.0 if fast else 160.0
    model_prices = []
    for _, row in df.iterrows():
        S = float(row["spot"])
        K = float(row["strike"])
        r = float(row["r"])
        q = float(row["q"])
        T = float(row["ttm_years"])
        call_price = heston_call_price(
            S, K, r, q, T, params, n_points=n_points, phi_max=phi_max
        )
        if row["put_call"].lower() == "call":
            model_prices.append(call_price)
        else:
            put_price = call_price - S * math.exp(-q * T) + K * math.exp(-r * T)
            model_prices.append(put_price)
    return np.array(model_prices)


def calibrate_surface(
    df: pd.DataFrame, config: CalibrationConfig
) -> tuple[dict, pd.DataFrame, dict]:
    df_prepared = _prepare_surface(df, config.fast)
    market_prices, vegas = _surface_market_prices(df_prepared)
    price_weights = _compute_weight_vector(
        df_prepared, market_prices, vegas, config.weight_mode
    )
    vol_weights = 1.0 / np.maximum(df_prepared["mid_iv"].to_numpy(), 1e-3)

    lb = np.array([0.05, 0.0005, 0.05, -0.95, 0.0005])
    ub = np.array([8.0, 0.5, 2.5, -0.05, 0.5])
    seeds = [
        np.array([1.5, 0.05, 0.4, -0.6, 0.04]),
        np.array([2.5, 0.08, 0.6, -0.7, 0.08]),
        np.array([0.8, 0.03, 0.3, -0.4, 0.02]),
    ]

    transform = ParameterTransform(config.param_transform, lb, ub)
    rng = np.random.default_rng(config.seed)
    best = None
    best_metrics = None
    best_internal = None
    attempts: list[dict] = []

    def residuals(z: np.ndarray) -> np.ndarray:
        params_vec = transform.from_internal(z)
        if not transform.within_bounds(params_vec):
            return np.ones_like(market_prices) * 1e4
        if np.any(~np.isfinite(params_vec)):
            return np.ones_like(market_prices) * 1e4
        params: Params = tuple(float(v) for v in params_vec)  # type: ignore
        kappa, theta, sigma, rho, v0 = params
        model_prices = _model_prices(df_prepared, params, fast=config.fast)
        if np.any(~np.isfinite(model_prices)):
            return np.ones_like(market_prices) * 1e4
        price_res = price_weights * (model_prices - market_prices)
        if config.metric == "vol":
            implied_model = [
                implied_vol_from_price(
                    model_prices[i],
                    float(df_prepared.iloc[i]["spot"]),
                    float(df_prepared.iloc[i]["strike"]),
                    float(df_prepared.iloc[i]["r"]),
                    float(df_prepared.iloc[i]["q"]),
                    float(df_prepared.iloc[i]["ttm_years"]),
                    df_prepared.iloc[i]["put_call"].lower() == "call",
                )
                for i in range(len(df_prepared))
            ]
            price_res = vol_weights * (
                np.array(implied_model) - df_prepared["mid_iv"].to_numpy()
            )
        feller_violation = max(0.0, sigma * sigma - 2.0 * kappa * theta)
        rho_penalty = max(0.0, abs(rho) - 0.93)
        return np.concatenate(
            [
                price_res,
                np.array([feller_violation * 10.0]),
                np.array([rho_penalty * 5.0]),
            ]
        )

    for trial in range(config.retries):
        base = np.clip(seeds[trial % len(seeds)], lb, ub)
        perturb = 1.0 + 0.15 * rng.standard_normal(size=5)
        candidate = np.clip(base * perturb, lb, ub)
        z0 = transform.to_internal(candidate)
        result = least_squares(
            residuals,
            z0,
            max_nfev=config.max_evals,
            verbose=0,
        )
        fitted_vec = transform.from_internal(result.x)
        params: Params = tuple(float(v) for v in fitted_vec)  # type: ignore
        kappa, theta, sigma, rho, v0 = params
        model_prices = _model_prices(df_prepared, params, fast=config.fast)
        rmse_price = float(np.sqrt(np.mean((model_prices - market_prices) ** 2)))
        model_vols = [
            implied_vol_from_price(
                model_prices[i],
                float(df_prepared.iloc[i]["spot"]),
                float(df_prepared.iloc[i]["strike"]),
                float(df_prepared.iloc[i]["r"]),
                float(df_prepared.iloc[i]["q"]),
                float(df_prepared.iloc[i]["ttm_years"]),
                df_prepared.iloc[i]["put_call"].lower() == "call",
            )
            for i in range(len(df_prepared))
        ]
        rmse_vol = float(
            np.sqrt(
                np.mean((np.array(model_vols) - df_prepared["mid_iv"].to_numpy()) ** 2)
            )
        )
        feller = 2.0 * kappa * theta - sigma * sigma
        market_iv = df_prepared["mid_iv"].to_numpy()
        abs_vol_error = np.abs(np.array(model_vols) - market_iv)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel_vol_error = abs_vol_error / np.maximum(market_iv, 1e-8)
        rmspe_vol = float(np.sqrt(np.mean(rel_vol_error * rel_vol_error)))
        abs_price_error = np.abs(model_prices - market_prices)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel_price_error = abs_price_error / np.maximum(market_prices, 1e-4)
        rmspe_price = float(np.sqrt(np.mean(rel_price_error * rel_price_error)))
        metrics = {
            "params": params,
            "rmse_price": rmse_price,
            "rmse_vol": rmse_vol,
            "rmspe_price": rmspe_price,
            "rmspe_price_pct": rmspe_price * 100.0,
            "rmspe_vol": rmspe_vol,
            "rmspe_vol_pct": rmspe_vol * 100.0,
            "feller": float(feller),
            "n_obs": int(len(df_prepared)),
            "n_strikes": int(df_prepared["strike"].nunique()),
            "n_maturities": int(df_prepared["ttm_years"].nunique()),
            "converged": bool(result.success),
            "cost": float(result.cost),
            "nit": int(result.nfev),
        }
        attempts.append(
            {
                "success": bool(result.success),
                "rmse_price": rmse_price,
                "rmse_vol": rmse_vol,
                "feller": float(feller),
                "nit": int(result.nfev),
            }
        )
        if best is None or rmse_vol < best_metrics["rmse_vol"]:
            best = params
            best_metrics = metrics
            best_internal = result.x

    assert best is not None and best_metrics is not None and best_internal is not None
    best_metrics["params"] = {
        "kappa": best[0],
        "theta": best[1],
        "sigma": best[2],
        "rho": best[3],
        "v0": best[4],
    }
    best_metrics["fast_mode"] = config.fast
    best_metrics["metric"] = config.metric
    residual_norm = float(np.linalg.norm(residuals(best_internal)))
    diagnostics = {
        "weight_mode": config.weight_mode,
        "param_transform": config.param_transform,
        "attempts": attempts,
        "residual_norm": residual_norm,
        "feller_violation": float(best_metrics["feller"]) < 0.0,
    }
    diagnostics["retry_failures"] = sum(
        1 for attempt in attempts if not attempt["success"]
    )
    diagnostics["warnings"] = []
    return best_metrics, df_prepared, diagnostics


def _plot_smiles(
    df: pd.DataFrame, model_vols: Iterable[float], output_path: Path
) -> None:
    df = df.copy()
    df["model_iv"] = list(model_vols)
    fig, ax = plt.subplots(figsize=(6, 4))
    for T, frame in df.groupby("ttm_years", sort=True):
        ax.plot(frame["strike"], frame["mid_iv"], "o-", label=f"{T:.2f}y market")
        ax.plot(frame["strike"], frame["model_iv"], "s--", label=f"{T:.2f}y model")
    ax.set_xlabel("Strike")
    ax.set_ylabel("Implied Volatility")
    ax.set_title("Heston Calibration: Market vs Model Smile")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_calibration_outputs(
    df: pd.DataFrame, metrics: dict, output_dir: Path, fast: bool
) -> dict:
    params = metrics["params"]
    params_tuple: Params = (
        float(params["kappa"]),
        float(params["theta"]),
        float(params["sigma"]),
        float(params["rho"]),
        float(params["v0"]),
    )
    model_prices = _model_prices(df, params_tuple, fast=fast)
    model_vols = [
        implied_vol_from_price(
            model_prices[i],
            float(df.iloc[i]["spot"]),
            float(df.iloc[i]["strike"]),
            float(df.iloc[i]["r"]),
            float(df.iloc[i]["q"]),
            float(df.iloc[i]["ttm_years"]),
            df.iloc[i]["put_call"].lower() == "call",
        )
        for i in range(len(df))
    ]
    date_str = df["date"].iloc[0].isoformat().replace("-", "")
    params_path = output_dir / f"params_{date_str}.json"
    fig_path = output_dir / f"fit_{date_str}.png"
    csv_path = output_dir / f"fit_{date_str}.csv"

    _plot_smiles(df, model_vols, fig_path)

    market_iv = df["mid_iv"].to_numpy()
    abs_vol_error = np.abs(np.array(model_vols) - market_iv)
    table = pd.DataFrame(
        {
            "strike": df["strike"].to_numpy(),
            "ttm": df["ttm_years"].to_numpy(),
            "market_iv": market_iv,
            "model_iv": model_vols,
            "abs_error": abs_vol_error,
        }
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_path, index=False, float_format="%.6f")

    metrics_out = dict(metrics)
    metrics_out["figure"] = str(fig_path)
    metrics_out["table"] = str(csv_path)
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(metrics_out, indent=2) + "\n")

    return {
        "params_path": params_path,
        "figure_path": fig_path,
        "table_path": csv_path,
        "model_vols": model_vols,
        "model_prices": model_prices,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Normalized option surface CSV")
    ap.add_argument(
        "--output-dir",
        default=str(ARTIFACTS_ROOT / "heston"),
        help="Directory for calibration artifacts",
    )
    ap.add_argument(
        "--metric",
        choices=["price", "vol"],
        default="price",
        help="Calibration loss metric",
    )
    ap.add_argument(
        "--fast", action="store_true", help="Reduce strikes/maturities for CI speed"
    )
    ap.add_argument("--seed", type=int, default=7, help="Random seed for restarts")
    ap.add_argument("--retries", type=int, default=4, help="Number of random restarts")
    ap.add_argument(
        "--max-evals",
        type=int,
        default=200,
        help="Max function evaluations per restart",
    )
    ap.add_argument(
        "--weight",
        choices=["iv", "vega", "bidask"],
        default="iv",
        help="Residual weighting scheme",
    )
    ap.add_argument(
        "--feller-warn",
        action="store_true",
        help="Emit warning if Feller condition is violated",
    )
    ap.add_argument(
        "--param-transform",
        choices=["none", "exp", "sigmoid"],
        default="none",
        help="Internal transform used for optimizer stability",
    )
    ap.add_argument(
        "--skip-manifest", action="store_true", help="Suppress manifest updates"
    )
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    config = CalibrationConfig(
        fast=args.fast,
        max_evals=args.max_evals,
        retries=args.retries,
        seed=args.seed,
        metric=args.metric,
        weight_mode=args.weight,
        feller_warn=args.feller_warn,
        param_transform=args.param_transform,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics, surface, diagnostics = calibrate_surface(df, config)
    metrics["weight_mode"] = config.weight_mode
    metrics["param_transform"] = config.param_transform
    metrics["diagnostics"] = diagnostics

    warnings: list[str] = []
    if config.feller_warn and float(metrics["feller"]) < 0.0:
        warnings.append(
            f"WARNING: Feller condition violated ({metrics['feller']:.4f}) for {surface['date'].iloc[0]}"
        )
        print(warnings[-1])

    metrics_with_input = dict(metrics)
    metrics_with_input["input"] = args.input
    outputs = save_calibration_outputs(
        surface, metrics_with_input, output_dir, args.fast
    )

    command = shlex.join([sys.executable] + sys.argv)
    manifest_entry = {
        "date": surface["date"].iloc[0].isoformat(),
        "input": args.input,
        "fast": bool(args.fast),
        "metric": args.metric,
        "seed": args.seed,
        "retries": args.retries,
        "max_evals": args.max_evals,
        "weight_mode": config.weight_mode,
        "param_transform": config.param_transform,
        "rmse_price": float(metrics["rmse_price"]),
        "rmse_vol": float(metrics["rmse_vol"]),
        "rmspe_price": float(metrics["rmspe_price"]),
        "rmspe_price_pct": float(metrics["rmspe_price_pct"]),
        "rmspe_vol": float(metrics["rmspe_vol"]),
        "rmspe_vol_pct": float(metrics["rmspe_vol_pct"]),
        "feller": float(metrics["feller"]),
        "n_obs": int(metrics["n_obs"]),
        "n_strikes": int(metrics["n_strikes"]),
        "n_maturities": int(metrics["n_maturities"]),
        "cost": float(metrics["cost"]),
        "nit": int(metrics["nit"]),
        "params": metrics["params"],
        "params_json": str(outputs["params_path"]),
        "figure": str(outputs["figure_path"]),
        "table": str(outputs["table_path"]),
        "inputs": describe_inputs([args.input]),
        "csv_rows": int(len(surface)),
        "command": command,
        "diagnostics": diagnostics,
        "warnings": warnings,
    }
    if not args.skip_manifest:
        update_run("heston", manifest_entry, append=True, id_field="date")

    params_path = outputs["params_path"]
    fig_path = outputs["figure_path"]
    csv_path = outputs["table_path"]
    print(f"Calibrated Heston params -> {params_path}")
    print(f"Smile figure -> {fig_path}")
    print(f"Data table -> {csv_path}")

    severe_failure = not config.fast and (
        float(metrics["rmse_vol"]) > 0.5
        or float(metrics["rmspe_price_pct"]) > 50.0
        or not bool(metrics["converged"])
    )
    if severe_failure:
        sys.stderr.write(
            "ERROR: Heston calibration did not meet accuracy thresholds.\n"
        )
        sys.exit(2)


if __name__ == "__main__":
    main()

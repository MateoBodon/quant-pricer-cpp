"""Independent QuantLib price and static-arbitrage checks for SSVI surfaces."""
from __future__ import annotations

import math
from typing import Dict

import numpy as np

from .bs_utils import bs_call
from .ssvi_surface import (
    SsviCalibrationConfig,
    SsviParameters,
    atm_total_variance,
    ssvi_total_variance,
)


def _quantlib() -> object:
    try:
        import QuantLib as ql
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("QuantLib is required for independent SSVI validation") from exc
    return ql


def quantlib_black_call_price(
    *,
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    volatility: float,
    maturity: float,
) -> float:
    """Return a Black call value from QuantLib's independent implementation."""
    values = (spot, strike, rate, dividend, volatility, maturity)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("QuantLib Black inputs must be finite")
    if spot <= 0.0 or strike <= 0.0 or volatility <= 0.0 or maturity <= 0.0:
        raise ValueError("spot, strike, volatility, and maturity must be positive")
    ql = _quantlib()
    discount = math.exp(-rate * maturity)
    forward = spot * math.exp((rate - dividend) * maturity)
    standard_deviation = volatility * math.sqrt(maturity)
    payoff = ql.PlainVanillaPayoff(ql.Option.Call, strike)
    calculator = ql.BlackCalculator(
        payoff,
        forward,
        standard_deviation,
        discount,
    )
    return float(calculator.value())


def quantlib_ssvi_arbitrage_audit(
    params: SsviParameters,
    config: SsviCalibrationConfig,
    *,
    maturity_grid_size: int = 9,
    log_moneyness_grid_size: int = 121,
) -> Dict[str, float | int | bool | str]:
    """Check prices, monotonicity, and convexity using QuantLib call values."""
    if maturity_grid_size < 3 or log_moneyness_grid_size < 11:
        raise ValueError("independent SSVI reference grids are too small")
    maturities = np.linspace(
        config.validation_t_min,
        config.validation_t_max,
        maturity_grid_size,
    )
    log_moneyness = np.linspace(
        config.validation_k_min,
        config.validation_k_max,
        log_moneyness_grid_size,
    )
    spot = 100.0
    rate = 0.03
    dividend = 0.01
    max_price_abs_error = 0.0
    max_monotonicity_violation = 0.0
    min_convex_slope_change = float("inf")
    invalid_price_count = 0

    for maturity in maturities:
        theta = float(atm_total_variance(maturity, params.theta_knots))
        total_variance = np.asarray(
            ssvi_total_variance(log_moneyness, theta, params),
            dtype=np.float64,
        )
        volatility = np.sqrt(total_variance / maturity)
        forward = spot * math.exp((rate - dividend) * maturity)
        strikes = forward * np.exp(log_moneyness)
        reference_prices = []
        for strike, vol in zip(strikes, volatility):
            reference = quantlib_black_call_price(
                spot=spot,
                strike=float(strike),
                rate=rate,
                dividend=dividend,
                volatility=float(vol),
                maturity=float(maturity),
            )
            repository = bs_call(
                spot,
                float(strike),
                rate,
                dividend,
                float(vol),
                float(maturity),
            )
            max_price_abs_error = max(
                max_price_abs_error,
                abs(reference - repository),
            )
            lower = max(
                0.0,
                spot * math.exp(-dividend * maturity)
                - float(strike) * math.exp(-rate * maturity),
            )
            upper = spot * math.exp(-dividend * maturity)
            if (
                not math.isfinite(reference)
                or reference < lower - 1e-10
                or reference > upper + 1e-10
            ):
                invalid_price_count += 1
            reference_prices.append(reference)
        prices = np.asarray(reference_prices, dtype=np.float64)
        max_monotonicity_violation = max(
            max_monotonicity_violation,
            float(np.max(np.diff(prices))),
        )
        slopes = np.diff(prices) / np.diff(strikes)
        min_convex_slope_change = min(
            min_convex_slope_change,
            float(np.min(np.diff(slopes))),
        )

    valid = bool(
        invalid_price_count == 0
        and max_price_abs_error <= 1e-10
        and max_monotonicity_violation <= 1e-10
        and min_convex_slope_change >= -1e-10
    )
    return {
        "status": "valid" if valid else "invalid",
        "valid": valid,
        "maturity_grid_size": maturity_grid_size,
        "log_moneyness_grid_size": log_moneyness_grid_size,
        "evaluated_price_count": maturity_grid_size * log_moneyness_grid_size,
        "invalid_price_count": invalid_price_count,
        "max_price_abs_error_vs_quantlib": max_price_abs_error,
        "max_call_monotonicity_violation": max_monotonicity_violation,
        "min_call_convex_slope_change": min_convex_slope_change,
    }

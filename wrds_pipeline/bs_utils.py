from __future__ import annotations

import math
from typing import Literal

OptionType = Literal["call", "put"]


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(spot: float, strike: float, rate: float, div: float, vol: float, T: float) -> float:
    if T <= 0.0:
        return max(spot - strike, 0.0)
    if vol <= 0.0:
        forward = spot * math.exp((rate - div) * T)
        return math.exp(-rate * T) * max(forward - strike, 0.0)
    sqrtT = math.sqrt(T)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * T) / (vol * sqrtT)
    d2 = d1 - vol * sqrtT
    return (
        spot * math.exp(-div * T) * _norm_cdf(d1)
        - strike * math.exp(-rate * T) * _norm_cdf(d2)
    )


def bs_put(spot: float, strike: float, rate: float, div: float, vol: float, T: float) -> float:
    call = bs_call(spot, strike, rate, div, vol, T)
    return call - spot * math.exp(-div * T) + strike * math.exp(-rate * T)


def bs_delta_call(spot: float, strike: float, rate: float, div: float, vol: float, T: float) -> float:
    if T <= 0.0 or spot <= 0.0 or strike <= 0.0:
        return 0.0
    sqrtT = math.sqrt(T)
    if vol <= 0.0:
        return 1.0 if spot > strike else 0.0
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * T) / (vol * sqrtT)
    return math.exp(-div * T) * _norm_cdf(d1)


def bs_vega(spot: float, strike: float, rate: float, div: float, vol: float, T: float) -> float:
    if T <= 0.0 or vol <= 0.0:
        return 0.0
    sqrtT = math.sqrt(T)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * T) / (vol * sqrtT)
    return spot * math.exp(-div * T) * math.sqrt(T) * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 * d1)


def implied_vol_from_price(
    price: float,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    option: OptionType = "call",
    tol: float = 1e-6,
    max_iter: int = 120,
) -> float:
    if price <= 0.0 or T <= 0.0:
        return 0.0

    def price_diff(vol: float) -> float:
        if option == "call":
            return bs_call(spot, strike, rate, div, vol, T) - price
        return bs_put(spot, strike, rate, div, vol, T) - price

    low, high = 1e-4, 4.0
    f_low = price_diff(low)
    f_high = price_diff(high)
    if f_low * f_high > 0:
        return max(0.5 * (low + high), 1e-4)

    mid = 0.5 * (low + high)
    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        f_mid = price_diff(mid)
        if abs(f_mid) < tol:
            return mid
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return mid

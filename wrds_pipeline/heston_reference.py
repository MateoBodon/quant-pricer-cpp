"""Independent QuantLib references for Heston European-call prices and deltas.

The production WRDS implementation uses the repository's characteristic
function.  This module deliberately constructs a separate QuantLib process and
analytic engine so reference agreement cannot be obtained by reusing the same
quadrature code.  Fractional aggregate maturities are linearly interpolated
between adjacent Actual/365 maturity dates and that approximation is reported
by callers as a reference limitation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Tuple


Params = Tuple[float, float, float, float, float]


@dataclass(frozen=True)
class ReferenceDelta:
    value: float
    coarse_value: float
    bump_stability_abs: float
    upper_bound: float


def _quantlib() -> object:
    try:
        import QuantLib as ql
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "QuantLib is required for independent Heston reference validation"
        ) from exc
    return ql


def _params_tuple(params: Mapping[str, float] | Params) -> Params:
    if isinstance(params, Mapping):
        values = (
            float(params["kappa"]),
            float(params["theta"]),
            float(params["sigma"]),
            float(params["rho"]),
            float(params["v0"]),
        )
    else:
        values = tuple(float(value) for value in params)
    if len(values) != 5 or not all(math.isfinite(value) for value in values):
        raise ValueError("Heston reference parameters must contain five finite values")
    return values  # type: ignore[return-value]


def _price_at_days(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    maturity_days: int,
    params: Params,
    integration_order: int,
) -> float:
    ql = _quantlib()
    reference_date = ql.Date(2, 1, 2020)
    ql.Settings.instance().evaluationDate = reference_date
    day_count = ql.Actual365Fixed()
    risk_free = ql.YieldTermStructureHandle(
        ql.FlatForward(reference_date, rate, day_count)
    )
    dividend = ql.YieldTermStructureHandle(
        ql.FlatForward(reference_date, div, day_count)
    )
    kappa, theta, sigma, rho, v0 = params
    process = ql.HestonProcess(
        risk_free,
        dividend,
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        v0,
        kappa,
        theta,
        sigma,
        rho,
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.Option.Call, strike),
        ql.EuropeanExercise(reference_date + int(maturity_days)),
    )
    option.setPricingEngine(
        ql.AnalyticHestonEngine(ql.HestonModel(process), integration_order)
    )
    return float(option.NPV())


def quantlib_heston_call_price(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Mapping[str, float] | Params,
    integration_order: int = 192,
) -> float:
    """Return an independent price at exact-day or interpolated Actual/365 time."""
    scalars = (spot, strike, rate, div, T)
    if not all(math.isfinite(float(value)) for value in scalars):
        raise ValueError("Heston reference market inputs must be finite")
    if spot <= 0.0 or strike <= 0.0:
        raise ValueError("spot and strike must be positive")
    if T <= 0.0:
        return max(spot - strike, 0.0)
    if integration_order < 32:
        raise ValueError("integration_order must be at least 32")

    param_tuple = _params_tuple(params)
    fractional_days = T * 365.0
    lower_days = max(1, int(math.floor(fractional_days)))
    upper_days = max(lower_days, int(math.ceil(fractional_days)))
    lower_price = _price_at_days(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        maturity_days=lower_days,
        params=param_tuple,
        integration_order=integration_order,
    )
    if upper_days == lower_days:
        return lower_price
    upper_price = _price_at_days(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        maturity_days=upper_days,
        params=param_tuple,
        integration_order=integration_order,
    )
    fraction = fractional_days - lower_days
    return float(lower_price + fraction * (upper_price - lower_price))


def quantlib_heston_delta(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Mapping[str, float] | Params,
    relative_bump: float = 1e-4,
    integration_order: int = 192,
) -> ReferenceDelta:
    """Return a bump-halving-checked QuantLib spot derivative."""
    if relative_bump <= 0.0:
        raise ValueError("relative_bump must be positive")

    def estimate(bump: float) -> float:
        up = quantlib_heston_call_price(
            spot=spot + bump,
            strike=strike,
            rate=rate,
            div=div,
            T=T,
            params=params,
            integration_order=integration_order,
        )
        down_spot = max(spot - bump, spot * 0.5)
        down = quantlib_heston_call_price(
            spot=down_spot,
            strike=strike,
            rate=rate,
            div=div,
            T=T,
            params=params,
            integration_order=integration_order,
        )
        return float((up - down) / ((spot + bump) - down_spot))

    coarse_bump = max(1e-5, abs(spot) * relative_bump)
    coarse = estimate(coarse_bump)
    refined = estimate(coarse_bump * 0.5)
    return ReferenceDelta(
        value=refined,
        coarse_value=coarse,
        bump_stability_abs=abs(refined - coarse),
        upper_bound=math.exp(-div * T),
    )

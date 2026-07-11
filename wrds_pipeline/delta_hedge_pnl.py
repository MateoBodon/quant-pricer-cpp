#!/usr/bin/env python3
"""Delta-hedged 1-day PnL simulation."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Tuple

import numpy as np
import pandas as pd

from .bs_utils import bs_delta_call
from .calibrate_heston import (
    REFERENCE_LAGUERRE_SCALE,
    REFERENCE_QUADRATURE_POINTS,
    heston_call_price,
)

DELTA_COL = "market_iv_bs_delta"
PNL_COL = "market_iv_bs_delta_pnl"
PNL_PER_TICK_COL = "market_iv_bs_delta_pnl_per_tick"
MEAN_PNL_COL = "market_iv_bs_delta_mean_pnl"
MEAN_TICKS_COL = "market_iv_bs_delta_mean_ticks"
SIGMA_COL = "market_iv_bs_delta_pnl_sigma"
HESTON_DELTA_COL = "calibrated_heston_delta"
HESTON_PNL_COL = "calibrated_heston_delta_pnl"
HESTON_PNL_PER_TICK_COL = "calibrated_heston_delta_pnl_per_tick"
HESTON_MEAN_PNL_COL = "calibrated_heston_delta_mean_pnl"
HESTON_MEAN_TICKS_COL = "calibrated_heston_delta_mean_ticks"
HESTON_SIGMA_COL = "calibrated_heston_delta_pnl_sigma"
HESTON_DELTA_CANDIDATE_COL = "calibrated_heston_delta_candidate"
HESTON_DELTA_STABILITY_COL = "calibrated_heston_delta_bump_stability_abs"
HESTON_DELTA_EVALUATED_COL = "calibrated_heston_delta_evaluated"
HESTON_DELTA_VALID_COL = "calibrated_heston_delta_valid"
HESTON_DELTA_INVALID_REASON_COL = "calibrated_heston_delta_invalid_reason"
HESTON_DELTA_EVALUATION_COUNT_COL = "calibrated_heston_delta_evaluation_count"
HESTON_DELTA_VALID_COUNT_COL = "calibrated_heston_delta_valid_count"
HESTON_DELTA_INVALID_COUNT_COL = "calibrated_heston_delta_invalid_count"


@dataclass(frozen=True)
class HestonDeltaDiagnostic:
    """Numerical evidence for one analytic-Heston spot derivative."""

    candidate: float
    primary_estimate: float
    stability_abs: float
    upper_bound: float
    valid: bool
    invalid_reasons: Tuple[str, ...]


def _central_heston_delta(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Tuple[float, float, float, float, float],
    bump: float,
    quadrature_points: int,
    laguerre_scale: float,
) -> float:
    spot_down = spot - bump
    if spot_down <= 0.0:
        spot_down = spot * 0.5
        bump = spot - spot_down
    price_up = heston_call_price(
        spot=spot + bump,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=params,
        n_points=quadrature_points,
        laguerre_scale=laguerre_scale,
    )
    price_down = heston_call_price(
        spot=spot_down,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=params,
        n_points=quadrature_points,
        laguerre_scale=laguerre_scale,
    )
    return float((price_up - price_down) / ((spot + bump) - spot_down))


def heston_delta_diagnostic(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Mapping[str, float],
    relative_bump: float = 1e-4,
    stability_abs_tolerance: float = 1e-4,
    stability_rel_tolerance: float = 5e-4,
    quadrature_points: int = REFERENCE_QUADRATURE_POINTS,
    laguerre_scale: float = REFERENCE_LAGUERRE_SCALE,
) -> HestonDeltaDiagnostic:
    """Evaluate a Heston delta without turning invalid numerics into a hedge.

    The refined central difference must agree with the original bump and obey
    the European-call no-arbitrage bounds ``[0, exp(-qT)]``.  Invalid estimates
    remain visible as diagnostics but are never clipped into admissibility.
    """
    scalar_inputs = (
        spot,
        strike,
        rate,
        div,
        T,
        relative_bump,
        laguerre_scale,
    )
    if not all(math.isfinite(float(value)) for value in scalar_inputs):
        raise ValueError("Heston delta inputs must be finite")
    if spot <= 0.0:
        raise ValueError("spot must be positive")
    if strike <= 0.0:
        raise ValueError("strike must be positive")
    if T < 0.0:
        raise ValueError("T must be non-negative")
    if relative_bump <= 0.0:
        raise ValueError("relative_bump must be positive")
    if quadrature_points < 16:
        raise ValueError("quadrature_points must be at least 16")
    if laguerre_scale <= 0.0:
        raise ValueError("laguerre_scale must be positive")
    if stability_abs_tolerance < 0.0 or stability_rel_tolerance < 0.0:
        raise ValueError("stability tolerances must be non-negative")

    param_tuple = (
        float(params["kappa"]),
        float(params["theta"]),
        float(params["sigma"]),
        float(params["rho"]),
        float(params["v0"]),
    )
    if not all(math.isfinite(value) for value in param_tuple):
        raise ValueError("Heston parameters must be finite")

    bump = max(1e-5, abs(spot) * relative_bump)
    primary = _central_heston_delta(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=param_tuple,
        bump=bump,
        quadrature_points=quadrature_points,
        laguerre_scale=laguerre_scale,
    )
    candidate = _central_heston_delta(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=param_tuple,
        bump=bump * 0.5,
        quadrature_points=quadrature_points,
        laguerre_scale=laguerre_scale,
    )
    upper = math.exp(-div * T)
    stability_abs = abs(candidate - primary)
    stability_limit = max(
        stability_abs_tolerance,
        stability_rel_tolerance * max(abs(candidate), abs(primary), 1.0),
    )

    invalid_reasons = []
    if not all(math.isfinite(value) for value in (primary, candidate, upper)):
        invalid_reasons.append("nonfinite_estimate")
    else:
        if primary < 0.0 or primary > upper or candidate < 0.0 or candidate > upper:
            invalid_reasons.append("no_arbitrage_bound_violation")
        if stability_abs > stability_limit:
            invalid_reasons.append("bump_instability")
    return HestonDeltaDiagnostic(
        candidate=candidate,
        primary_estimate=primary,
        stability_abs=stability_abs,
        upper_bound=upper,
        valid=not invalid_reasons,
        invalid_reasons=tuple(invalid_reasons),
    )


def heston_delta_call(
    *,
    spot: float,
    strike: float,
    rate: float,
    div: float,
    T: float,
    params: Mapping[str, float],
    relative_bump: float = 1e-4,
    quadrature_points: int = REFERENCE_QUADRATURE_POINTS,
    laguerre_scale: float = REFERENCE_LAGUERRE_SCALE,
) -> float:
    """Return a validated central-difference Heston delta or fail closed."""
    diagnostic = heston_delta_diagnostic(
        spot=spot,
        strike=strike,
        rate=rate,
        div=div,
        T=T,
        params=params,
        relative_bump=relative_bump,
        quadrature_points=quadrature_points,
        laguerre_scale=laguerre_scale,
    )
    if not diagnostic.valid:
        reasons = ",".join(diagnostic.invalid_reasons)
        raise ValueError(f"invalid analytic Heston delta: {reasons}")
    return float(diagnostic.candidate)


def summarize_heston_delta_numerics(detail: pd.DataFrame) -> Dict[str, object]:
    """Return aggregate-safe numerical validity evidence for one fit date."""
    if detail.empty or HESTON_DELTA_EVALUATED_COL not in detail.columns:
        return {
            "status": "not_evaluated",
            "evaluated_surface_rows": 0,
            "valid_surface_rows": 0,
            "invalid_surface_rows": 0,
            "evaluated_quote_weight": 0,
            "valid_quote_weight": 0,
            "invalid_quote_weight": 0,
            "invalid_reason_counts": {},
        }

    evaluated = detail[HESTON_DELTA_EVALUATED_COL].fillna(False).astype(bool)
    valid = detail[HESTON_DELTA_VALID_COL].fillna(False).astype(bool) & evaluated
    invalid = evaluated & ~valid
    quote_weight = detail["quotes"].clip(lower=1).fillna(1).astype(int)
    reason_counts = (
        detail.loc[invalid, HESTON_DELTA_INVALID_REASON_COL]
        .fillna("unspecified")
        .value_counts()
        .sort_index()
    )
    evaluated_rows = int(evaluated.sum())
    invalid_rows = int(invalid.sum())
    status = "valid" if evaluated_rows and invalid_rows == 0 else "invalid"
    if evaluated_rows == 0:
        status = "not_evaluated"
    return {
        "status": status,
        "evaluated_surface_rows": evaluated_rows,
        "valid_surface_rows": int(valid.sum()),
        "invalid_surface_rows": invalid_rows,
        "evaluated_quote_weight": int(quote_weight[evaluated].sum()),
        "valid_quote_weight": int(quote_weight[valid].sum()),
        "invalid_quote_weight": int(quote_weight[invalid].sum()),
        "invalid_reason_counts": {
            str(reason): int(count) for reason, count in reason_counts.items()
        },
    }


def simulate(
    today: pd.DataFrame,
    tomorrow: pd.DataFrame,
    *,
    heston_params: Mapping[str, float] | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    merged = pd.merge(
        today,
        tomorrow,
        on=["tenor_bucket", "moneyness"],
        suffixes=("_t", "_t1"),
    )
    if merged.empty:
        detail_cols = [
            "tenor_bucket",
            "moneyness",
            DELTA_COL,
            PNL_COL,
            PNL_PER_TICK_COL,
            HESTON_DELTA_COL,
            HESTON_DELTA_CANDIDATE_COL,
            HESTON_DELTA_STABILITY_COL,
            HESTON_DELTA_EVALUATED_COL,
            HESTON_DELTA_VALID_COL,
            HESTON_DELTA_INVALID_REASON_COL,
            HESTON_PNL_COL,
            HESTON_PNL_PER_TICK_COL,
            "quotes",
        ]
        summary_cols = [
            "tenor_bucket",
            MEAN_PNL_COL,
            MEAN_TICKS_COL,
            SIGMA_COL,
            HESTON_MEAN_PNL_COL,
            HESTON_MEAN_TICKS_COL,
            HESTON_SIGMA_COL,
            HESTON_DELTA_EVALUATION_COUNT_COL,
            HESTON_DELTA_VALID_COUNT_COL,
            HESTON_DELTA_INVALID_COUNT_COL,
            "count",
        ]
        return pd.DataFrame(columns=detail_cols), pd.DataFrame(columns=summary_cols)

    spot_t = float(today["spot"].mean())
    spot_t1 = float(tomorrow["spot"].mean())
    spot_change = spot_t1 - spot_t

    def _delta(row) -> float:
        return bs_delta_call(
            spot=spot_t,
            strike=float(row["strike_t"]),
            rate=float(row["rate_t"]),
            div=float(row["dividend_t"]),
            vol=float(row["mid_iv_t"]),
            T=float(row["ttm_years_t"]),
        )

    merged[DELTA_COL] = merged.apply(_delta, axis=1)
    merged[PNL_COL] = (merged["mid_price_t1"] - merged["mid_price_t"]) - merged[
        DELTA_COL
    ] * spot_change
    merged[PNL_PER_TICK_COL] = merged[PNL_COL] / 0.05
    if heston_params is None:
        merged[HESTON_DELTA_COL] = np.nan
        merged[HESTON_DELTA_CANDIDATE_COL] = np.nan
        merged[HESTON_DELTA_STABILITY_COL] = np.nan
        merged[HESTON_DELTA_EVALUATED_COL] = False
        merged[HESTON_DELTA_VALID_COL] = False
        merged[HESTON_DELTA_INVALID_REASON_COL] = "not_evaluated"
        merged[HESTON_PNL_COL] = np.nan
        merged[HESTON_PNL_PER_TICK_COL] = np.nan
    else:
        def _heston_diagnostic(row: pd.Series) -> pd.Series:
            diagnostic = heston_delta_diagnostic(
                spot=spot_t,
                strike=float(row["strike_t"]),
                rate=float(row["rate_t"]),
                div=float(row["dividend_t"]),
                T=float(row["ttm_years_t"]),
                params=heston_params,
            )
            return pd.Series(
                {
                    HESTON_DELTA_COL: (
                        diagnostic.candidate if diagnostic.valid else np.nan
                    ),
                    HESTON_DELTA_CANDIDATE_COL: diagnostic.candidate,
                    HESTON_DELTA_STABILITY_COL: diagnostic.stability_abs,
                    HESTON_DELTA_EVALUATED_COL: True,
                    HESTON_DELTA_VALID_COL: diagnostic.valid,
                    HESTON_DELTA_INVALID_REASON_COL: ",".join(
                        diagnostic.invalid_reasons
                    ),
                }
            )

        diagnostic_columns = merged.apply(
            _heston_diagnostic,
            axis=1,
        )
        for column in diagnostic_columns.columns:
            merged[column] = diagnostic_columns[column]
        merged[HESTON_PNL_COL] = (
            merged["mid_price_t1"] - merged["mid_price_t"]
        ) - merged[HESTON_DELTA_COL] * spot_change
        merged[HESTON_PNL_PER_TICK_COL] = merged[HESTON_PNL_COL] / 0.05
    merged["quotes"] = merged["quotes_t"]

    detail = merged[
        [
            "tenor_bucket",
            "moneyness",
            DELTA_COL,
            PNL_COL,
            PNL_PER_TICK_COL,
            HESTON_DELTA_COL,
            HESTON_DELTA_CANDIDATE_COL,
            HESTON_DELTA_STABILITY_COL,
            HESTON_DELTA_EVALUATED_COL,
            HESTON_DELTA_VALID_COL,
            HESTON_DELTA_INVALID_REASON_COL,
            HESTON_PNL_COL,
            HESTON_PNL_PER_TICK_COL,
            "quotes",
        ]
    ].copy()

    exploded = detail.loc[
        detail.index.repeat(detail["quotes"].clip(lower=1).astype(int))
    ].reset_index(drop=True)
    if exploded.empty:
        summary = pd.DataFrame(
            columns=[
                "tenor_bucket",
                MEAN_PNL_COL,
                MEAN_TICKS_COL,
                SIGMA_COL,
                HESTON_MEAN_PNL_COL,
                HESTON_MEAN_TICKS_COL,
                HESTON_SIGMA_COL,
                HESTON_DELTA_EVALUATION_COUNT_COL,
                HESTON_DELTA_VALID_COUNT_COL,
                HESTON_DELTA_INVALID_COUNT_COL,
                "count",
            ]
        )
    else:
        summary = exploded.groupby("tenor_bucket", as_index=False, observed=True).agg(
            **{
                MEAN_PNL_COL: (PNL_COL, "mean"),
                MEAN_TICKS_COL: (PNL_PER_TICK_COL, "mean"),
                SIGMA_COL: (PNL_PER_TICK_COL, "std"),
                HESTON_MEAN_PNL_COL: (HESTON_PNL_COL, "mean"),
                HESTON_MEAN_TICKS_COL: (HESTON_PNL_PER_TICK_COL, "mean"),
                HESTON_SIGMA_COL: (HESTON_PNL_PER_TICK_COL, "std"),
                HESTON_DELTA_EVALUATION_COUNT_COL: (
                    HESTON_DELTA_EVALUATED_COL,
                    "sum",
                ),
                HESTON_DELTA_VALID_COUNT_COL: (HESTON_DELTA_VALID_COL, "sum"),
                "count": (PNL_COL, "size"),
            }
        )
        summary[HESTON_DELTA_INVALID_COUNT_COL] = (
            summary[HESTON_DELTA_EVALUATION_COUNT_COL]
            - summary[HESTON_DELTA_VALID_COUNT_COL]
        )
        incomplete = (
            summary[HESTON_DELTA_EVALUATION_COUNT_COL] == 0
        ) | (summary[HESTON_DELTA_INVALID_COUNT_COL] > 0)
        summary.loc[
            incomplete,
            [HESTON_MEAN_PNL_COL, HESTON_MEAN_TICKS_COL, HESTON_SIGMA_COL],
        ] = np.nan
    fill_columns = [MEAN_PNL_COL, MEAN_TICKS_COL, SIGMA_COL]
    for col in fill_columns:
        summary[col] = summary[col].fillna(0.0)
    return detail, summary


def write_outputs(
    detail_csv: Path, summary_csv: Path, detail: pd.DataFrame, summary: pd.DataFrame
) -> None:
    detail_csv.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(detail_csv, index=False)
    summary.to_csv(summary_csv, index=False)

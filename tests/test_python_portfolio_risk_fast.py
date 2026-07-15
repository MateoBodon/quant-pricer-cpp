#!/usr/bin/env python3
"""Independent QuantLib and API-contract checks for native portfolio risk."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import QuantLib as ql


POSITION_COLUMNS = ("price", "value", "delta", "gamma", "vega", "theta", "rho")
TOTAL_COLUMNS = ("value", "delta", "gamma", "vega", "theta", "rho")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def quantlib_metrics(row: np.ndarray) -> np.ndarray:
    option_type, quantity, spot, strike, rate, dividend, volatility, time = row
    evaluation_date = ql.Date(15, ql.July, 2026)
    ql.Settings.instance().evaluationDate = evaluation_date
    days = int(round(float(time) * 365.0))
    if days == 0:
        price = max(0.0, spot - strike) if option_type == 1.0 else max(0.0, strike - spot)
        delta = 1.0 if option_type == 1.0 and spot > strike else 0.0
        if option_type == -1.0:
            delta = -1.0 if spot < strike else 0.0
        return np.array([price, quantity * price, quantity * delta, 0.0, 0.0, 0.0, 0.0])
    day_count = ql.Actual365Fixed()
    risk_free = ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, float(rate), day_count))
    dividend_curve = ql.YieldTermStructureHandle(ql.FlatForward(evaluation_date, float(dividend), day_count))
    vol_curve = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(evaluation_date, ql.NullCalendar(), float(volatility), day_count)
    )
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(float(spot))), dividend_curve, risk_free, vol_curve
    )
    payoff_type = ql.Option.Call if option_type == 1.0 else ql.Option.Put
    option = ql.VanillaOption(ql.PlainVanillaPayoff(payoff_type, float(strike)), ql.EuropeanExercise(evaluation_date + days))
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    price = option.NPV()
    return np.array(
        [price, quantity * price, quantity * option.delta(), quantity * option.gamma(),
         quantity * option.vega(), quantity * option.theta(), quantity * option.rho()],
        dtype=np.float64,
    )


def deterministic_positions() -> np.ndarray:
    rows: list[list[float]] = []
    ratios = (0.72, 0.95, 1.0, 1.08, 1.35)
    days = (7, 30, 91, 365, 730)
    for index in range(60):
        option_type = 1.0 if index % 2 == 0 else -1.0
        strike = 80.0 + 5.0 * (index % 9)
        spot = strike * ratios[index % len(ratios)]
        quantity = (-1.0 if index % 3 == 0 else 1.0) * (0.25 + (index % 7))
        rate = (-0.005, 0.0, 0.02, 0.07)[index % 4]
        dividend = (0.0, 0.01, 0.035)[index % 3]
        volatility = (0.08, 0.18, 0.35, 0.8)[index % 4]
        rows.append([option_type, quantity, spot, strike, rate, dividend, volatility, days[index % 5] / 365.0])
    return np.asarray(rows, dtype=np.float64)


def main() -> int:
    args = parse_args()
    sys.path.insert(0, str(args.module_dir.resolve()))
    import pyquant_pricer as qp

    positions = deterministic_positions()
    result = qp.bs_portfolio_risk(positions)
    assert tuple(result["position_columns"]) == POSITION_COLUMNS
    assert tuple(result["total_columns"]) == TOTAL_COLUMNS
    actual = np.asarray(result["position_metrics"])
    reference = np.vstack([quantlib_metrics(row) for row in positions])
    metric_max_abs = dict(
        zip(POSITION_COLUMNS, np.max(np.abs(actual - reference), axis=0))
    )
    np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-10)
    sequential_totals = np.zeros(6, dtype=np.float64)
    for row in actual:
        sequential_totals += row[1:]
    np.testing.assert_array_equal(result["portfolio_totals"], sequential_totals)

    scenario_positions = positions[:12].copy()
    shocks = np.asarray(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [-0.20, 0.12, 0.015, 0.0, 1.0 / 365.0],
            [-0.08, 0.05, -0.01, 0.003, 5.0 / 365.0],
            [0.07, -0.03, 0.005, -0.002, 2.0 / 365.0],
            [0.18, 0.02, 0.025, 0.01, 7.0 / 365.0],
            [-0.35, 0.25, -0.02, 0.0, 6.0 / 365.0],
        ],
        dtype=np.float64,
    )
    scenario_result = qp.bs_portfolio_scenarios(scenario_positions, shocks, detail=True)
    base = np.vstack([quantlib_metrics(row) for row in scenario_positions])[:, 1]
    reference_detail = np.empty((len(shocks), len(scenario_positions)))
    for scenario_index, shock in enumerate(shocks):
        shocked = scenario_positions.copy()
        shocked[:, 2] *= 1.0 + shock[0]
        shocked[:, 4] += shock[2]
        shocked[:, 5] += shock[3]
        shocked[:, 6] += shock[1]
        shocked[:, 7] = np.maximum(0.0, shocked[:, 7] - shock[4])
        reference_detail[scenario_index] = np.vstack([quantlib_metrics(row) for row in shocked])[:, 1] - base
    np.testing.assert_allclose(scenario_result["position_pnl"], reference_detail, rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose(
        scenario_result["portfolio_pnl"], reference_detail.sum(axis=1), rtol=1e-10, atol=1e-9
    )
    scenario_position_max_abs = float(np.max(np.abs(scenario_result["position_pnl"] - reference_detail)))
    scenario_portfolio_max_abs = float(
        np.max(np.abs(scenario_result["portfolio_pnl"] - reference_detail.sum(axis=1)))
    )
    np.testing.assert_array_equal(scenario_result["portfolio_pnl"][0], np.array(0.0))
    aggregate_only = qp.bs_portfolio_scenarios(scenario_positions, shocks, detail=False)
    assert aggregate_only["position_pnl"] is None
    np.testing.assert_array_equal(aggregate_only["portfolio_pnl"], scenario_result["portfolio_pnl"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda _: qp.bs_portfolio_scenarios(scenario_positions, shocks, False)["portfolio_pnl"], range(32)))
    for output in outputs:
        np.testing.assert_array_equal(output, scenario_result["portfolio_pnl"])

    invalid_cases = [
        np.ones((2, 7)),
        np.array([[0.0, 1.0, 100.0, 100.0, 0.01, 0.0, 0.2, 1.0]]),
        np.array([[1.0, 1.0, math.nan, 100.0, 0.01, 0.0, 0.2, 1.0]]),
        np.array([[1.0, 1.0, 100.0, 100.0, 0.01, 0.0, -0.2, 1.0]]),
    ]
    for invalid in invalid_cases:
        try:
            qp.bs_portfolio_risk(invalid)
        except (ValueError, RuntimeError):
            pass
        else:
            raise AssertionError(f"invalid position input did not fail closed: {invalid!r}")

    try:
        qp.bs_portfolio_scenarios(scenario_positions, np.array([[0.0, -1.0, 0.0, 0.0, 0.0]]), False)
    except (ValueError, RuntimeError):
        pass
    else:
        raise AssertionError("negative post-shock volatility did not fail closed")
    if args.json_out is not None:
        payload = {
            "schema_version": 1,
            "evaluator_id": "bs_portfolio_quantlib_parity_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "position_case_count": len(positions),
            "scenario_cell_count": len(shocks) * len(scenario_positions),
            "price_greek_tolerance": {"absolute": 1e-10, "relative": 1e-10},
            "scenario_pnl_tolerance": {"absolute": 1e-9, "relative": 1e-10},
            "metric_max_abs_error": {key: float(value) for key, value in metric_max_abs.items()},
            "scenario_position_pnl_max_abs_error": scenario_position_max_abs,
            "scenario_portfolio_pnl_max_abs_error": scenario_portfolio_max_abs,
            "zero_shock_exact": bool(scenario_result["portfolio_pnl"][0] == 0.0),
            "concurrent_replays": 32,
            "concurrent_replays_bitwise_identical": True,
            "invalid_position_cases_rejected": len(invalid_cases),
            "invalid_post_shock_case_rejected": True,
            "quantlib_version": ql.__version__,
            "pyquant_pricer_version": qp.__version__,
            "claim_boundary": (
                "Independent deterministic Black-Scholes parity only; no forecast, hedge, market-risk, PnL, or trading claim."
            ),
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"portfolio QuantLib oracle: {len(positions)} positions and "
        f"{len(shocks) * len(scenario_positions)} scenario cells passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

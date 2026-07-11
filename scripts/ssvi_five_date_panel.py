#!/usr/bin/env python3
"""Run the predeclared five-date SSVI/Heston/BS development panel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import numpy as np

from ssvi_development_benchmark import (
    INSAMPLE_METRICS,
    OOS_METRICS,
    _date_result,
)

PANEL_ENTRIES = (
    ("2020-03-16", "2020-03-17", "stress-covid-a", "stress"),
    ("2020-03-17", "2020-03-18", "stress-covid-b", "stress"),
    ("2022-06-13", "2022-06-14", "calm-inflation-a", "calm"),
    ("2022-06-14", "2022-06-15", "calm-inflation-b", "calm"),
    ("2024-06-14", "2024-06-17", "calm-june", "calm"),
)
MODEL_NAMES = ("ssvi", "heston", "tenor_flat_bs")
METRIC_SPECS = tuple(
    [("insample", metric) for metric in INSAMPLE_METRICS]
    + [("oos", metric) for metric in OOS_METRICS]
)


def _metric(item: Dict[str, object], model: str, scope: str, metric: str) -> float:
    return float(item["models"][model][scope][metric])


def _metric_key(scope: str, metric: str) -> str:
    return f"{scope}_{metric}"


def _stability(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for model in MODEL_NAMES:
        model_metrics = {}
        for scope, metric in METRIC_SPECS:
            values = np.asarray(
                [_metric(item, model, scope, metric) for item in per_date],
                dtype=np.float64,
            )
            worst_index = int(np.argmax(values))
            best_index = int(np.argmin(values))
            mean = float(np.mean(values))
            standard_deviation = float(np.std(values, ddof=0))
            model_metrics[_metric_key(scope, metric)] = {
                "mean": mean,
                "median": float(np.median(values)),
                "standard_deviation": standard_deviation,
                "coefficient_of_variation": (
                    standard_deviation / abs(mean) if mean != 0.0 else None
                ),
                "best": float(values[best_index]),
                "best_trade_date": per_date[best_index]["trade_date"],
                "worst": float(values[worst_index]),
                "worst_trade_date": per_date[worst_index]["trade_date"],
            }
        result[model] = model_metrics
    return result


def _regime_metrics(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    result = {}
    for regime in ("stress", "calm"):
        subset = [item for item in per_date if item["regime"] == regime]
        models = {}
        for model in MODEL_NAMES:
            metrics = {}
            for scope, metric in METRIC_SPECS:
                values = [_metric(item, model, scope, metric) for item in subset]
                metrics[_metric_key(scope, metric)] = {
                    "median": float(np.median(values)),
                    "mean": float(np.mean(values)),
                    "date_count": len(values),
                }
            models[model] = metrics
        result[regime] = models
    return result


def _paired_ssvi_comparison(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    result = {}
    for comparator in ("heston", "tenor_flat_bs"):
        metrics = {}
        for scope, metric in METRIC_SPECS:
            relative_changes = []
            win_dates = []
            for item in per_date:
                ssvi_value = _metric(item, "ssvi", scope, metric)
                comparator_value = _metric(item, comparator, scope, metric)
                relative_changes.append(
                    (ssvi_value / comparator_value - 1.0) * 100.0
                )
                if ssvi_value < comparator_value:
                    win_dates.append(item["trade_date"])
            metrics[_metric_key(scope, metric)] = {
                "median_relative_change_percent": float(
                    np.median(relative_changes)
                ),
                "mean_relative_change_percent": float(np.mean(relative_changes)),
                "ssvi_win_count": len(win_dates),
                "ssvi_win_dates": win_dates,
                "date_count": len(per_date),
            }
        result[comparator] = metrics
    return result


def _winner_counts(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    counts = {model: 0 for model in MODEL_NAMES}
    by_metric = {}
    for scope, metric in METRIC_SPECS:
        key = _metric_key(scope, metric)
        metric_counts = {model: 0 for model in MODEL_NAMES}
        for item in per_date:
            winner = str(item["metric_winners"][key])
            counts[winner] += 1
            metric_counts[winner] += 1
        by_metric[key] = metric_counts
    return {
        "overall": counts,
        "by_metric": by_metric,
        "comparison_count": len(per_date) * len(METRIC_SPECS),
    }


def _hedge_aggregate(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    numerical = [
        item["hedge_diagnostics"]["heston_delta_numerics"] for item in per_date
    ]
    all_valid = all(item["status"] == "valid" for item in numerical)
    methods = {}
    for key in (
        "market_iv_bs_delta_pnl_ticks",
        "calibrated_heston_delta_pnl_ticks",
    ):
        date_means = [
            item["hedge_diagnostics"][key]["mean"] for item in per_date
        ]
        date_sigmas = [
            item["hedge_diagnostics"][key]["sigma"] for item in per_date
        ]
        if any(value is None for value in date_means + date_sigmas):
            methods[key] = {
                "status": "invalid",
                "median_date_mean_ticks": None,
                "median_date_sigma_ticks": None,
            }
            continue
        methods[key] = {
            "status": "valid",
            "median_date_mean_ticks": float(np.median(date_means)),
            "median_date_sigma_ticks": float(np.median(date_sigmas)),
            "date_mean_ticks_standard_deviation": float(
                np.std(date_means, ddof=0)
            ),
            "date_sigma_ticks_standard_deviation": float(
                np.std(date_sigmas, ddof=0)
            ),
        }
    return {
        "scope": "one_day_delta_hedge_diagnostic_not_return_or_strategy_pnl",
        "heston_all_numerical_gates_pass": all_valid,
        "evaluated_surface_rows": int(
            sum(item["evaluated_surface_rows"] for item in numerical)
        ),
        "invalid_surface_rows": int(
            sum(item["invalid_surface_rows"] for item in numerical)
        ),
        "evaluated_quote_weight": int(
            sum(item["evaluated_quote_weight"] for item in numerical)
        ),
        "invalid_quote_weight": int(
            sum(item["invalid_quote_weight"] for item in numerical)
        ),
        "methods": methods,
        "ssvi_delta_pnl": "not_evaluated",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = args.run_root.resolve()
    per_date = [
        _date_result(
            run_root,
            trade_date,
            next_trade_date,
            label=label,
            regime=regime,
            include_hedge=True,
        )
        for trade_date, next_trade_date, label, regime in PANEL_ENTRIES
    ]
    insample_rows = sum(int(item["insample_surface_rows"]) for item in per_date)
    if insample_rows != 1239:
        raise RuntimeError(
            f"predeclared panel expected 1239 in-sample rows, got {insample_rows}"
        )
    all_ssvi_valid = all(
        item["models"]["ssvi"]["promotion_status"] == "eligible"
        and item["models"]["ssvi"]["calibration_diagnostics"]["arbitrage"][
            "analytic_sufficient_conditions_pass"
        ]
        and item["models"]["ssvi"]["calibration_diagnostics"]["arbitrage"][
            "numerical_static_arbitrage_pass"
        ]
        and item["models"]["ssvi"]["independent_reference"]["status"] == "valid"
        for item in per_date
    )
    hedge = _hedge_aggregate(per_date)
    payload = {
        "schema_version": 1,
        "status": (
            "development_valid"
            if all_ssvi_valid and hedge["heston_all_numerical_gates_pass"]
            else "diagnostic_only"
        ),
        "claim_scope": "fixed_five_date_development_panel_not_superiority",
        "input_run_id": run_root.name,
        "panel_id": "wrds_panel_calm_stress_v1",
        "data_policy": "aggregate_only_no_option_rows_or_parameters",
        "predeclared_entries": [list(entry) for entry in PANEL_ENTRIES],
        "date_count": len(per_date),
        "regime_date_counts": {"stress": 2, "calm": 3},
        "insample_surface_rows": insample_rows,
        "oos_surface_rows": sum(
            int(item["oos_surface_rows"]) for item in per_date
        ),
        "ssvi_all_arbitrage_and_reference_gates_pass": all_ssvi_valid,
        "winner_counts": _winner_counts(per_date),
        "stability": _stability(per_date),
        "regime_metrics": _regime_metrics(per_date),
        "paired_ssvi_comparison": _paired_ssvi_comparison(per_date),
        "hedge_diagnostics": hedge,
        "per_date": per_date,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

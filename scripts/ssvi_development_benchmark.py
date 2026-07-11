#!/usr/bin/env python3
"""Compare SSVI, repaired Heston, and tenor-flat BS on fixed dev dates.

Only aggregate metrics and diagnostics are written.  The two date pairs are
predeclared and deliberately enforced so this command cannot silently become a
broad restricted-data model-selection sweep.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wrds_pipeline import (  # noqa: E402
    calibrate_bs,
    calibrate_heston,
    delta_hedge_pnl,
)
from wrds_pipeline.ssvi_reference import (  # noqa: E402
    quantlib_ssvi_arbitrage_audit,
)
from wrds_pipeline.ssvi_surface import (  # noqa: E402
    SsviCalibrationConfig,
    apply_surface as apply_ssvi_surface,
    calibrate as calibrate_ssvi,
    summarize_oos as summarize_ssvi_oos,
)

PREDECLARED_PAIRS = (
    ("2020-03-16", "2020-03-17"),
    ("2024-06-14", "2024-06-17"),
)
INSAMPLE_METRICS = (
    "iv_rmse_volpts_vega_wt",
    "iv_mae_volpts_vega_wt",
    "iv_p90_bps",
    "price_rmse_ticks",
)
OOS_METRICS = ("iv_mae_bps", "price_mae_ticks")


def _float_metrics(payload: Dict[str, object], keys: tuple[str, ...]) -> Dict[str, float]:
    return {key: float(payload[key]) for key in keys}


def _generic_oos(surface: pd.DataFrame) -> Dict[str, float | int]:
    weights = calibrate_heston._vega_quote_weights(surface)
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


def _frequency_weighted_stats(
    values: pd.Series,
    frequency: pd.Series,
) -> Dict[str, float | int | None]:
    numeric = values.to_numpy(np.float64)
    weights = frequency.to_numpy(np.float64)
    valid = np.isfinite(numeric) & np.isfinite(weights) & (weights > 0.0)
    if not valid.any():
        return {"mean": None, "sigma": None, "quote_weight": 0}
    numeric = numeric[valid]
    weights = weights[valid]
    total_weight = float(weights.sum())
    mean = float(np.average(numeric, weights=weights))
    variance_numerator = float(np.sum(weights * np.square(numeric - mean)))
    sigma = (
        math.sqrt(variance_numerator / (total_weight - 1.0))
        if total_weight > 1.0
        else 0.0
    )
    return {
        "mean": mean,
        "sigma": sigma,
        "quote_weight": int(total_weight),
    }


def _hedge_diagnostics(
    today: pd.DataFrame,
    next_surface: pd.DataFrame,
    heston_params: Dict[str, float],
) -> Dict[str, object]:
    detail, _ = delta_hedge_pnl.simulate(
        today,
        next_surface,
        heston_params=heston_params,
    )
    numerical = delta_hedge_pnl.summarize_heston_delta_numerics(detail)
    market = _frequency_weighted_stats(
        detail[delta_hedge_pnl.PNL_PER_TICK_COL],
        detail["quotes"],
    )
    heston = _frequency_weighted_stats(
        detail[delta_hedge_pnl.HESTON_PNL_PER_TICK_COL],
        detail["quotes"],
    )
    if numerical["status"] != "valid":
        heston = {
            "mean": None,
            "sigma": None,
            "quote_weight": int(numerical["valid_quote_weight"]),
        }
    return {
        "scope": "one_day_delta_hedge_diagnostic_not_return_or_strategy_pnl",
        "matched_surface_rows": int(len(detail)),
        "heston_delta_numerics": numerical,
        "market_iv_bs_delta_pnl_ticks": market,
        "calibrated_heston_delta_pnl_ticks": heston,
        "ssvi_delta_pnl": "not_evaluated",
    }


def _date_result(
    run_root: Path,
    trade_date: str,
    next_date: str,
    *,
    label: str | None = None,
    regime: str | None = None,
    include_hedge: bool = False,
) -> Dict[str, object]:
    date_root = run_root / "per_date" / trade_date
    today = pd.read_csv(date_root / f"spx_{trade_date}_surface.csv")
    next_surface = pd.read_csv(date_root / f"spx_{next_date}_surface.csv")

    ssvi_config = SsviCalibrationConfig(max_evals=500, multistart=True)
    ssvi = calibrate_ssvi(today, ssvi_config)
    ssvi_oos_surface = apply_ssvi_surface(next_surface, ssvi["params"])
    ssvi_reference = quantlib_ssvi_arbitrage_audit(
        ssvi["params"],
        ssvi_config,
    )

    heston = calibrate_heston.calibrate(
        today,
        calibrate_heston.CalibrationConfig(
            fast=False,
            max_evals=160,
            bootstrap_samples=0,
            rng_seed=19,
            multistart=True,
        ),
    )
    heston_oos_surface = calibrate_heston.apply_model(
        next_surface,
        heston["params"],
    )

    bs = calibrate_bs.fit_bs(today)
    bs_fit_vols = bs.surface.groupby("tenor_bucket", observed=True)[
        "fit_vol"
    ].first()
    bs_oos_surface = calibrate_bs.evaluate_oos(next_surface, bs_fit_vols)

    models: Dict[str, Dict[str, object]] = {
        "ssvi": {
            "insample": _float_metrics(ssvi["metrics"], INSAMPLE_METRICS),
            "oos": summarize_ssvi_oos(ssvi_oos_surface),
            "promotion_status": ssvi["diagnostics"]["promotion_status"],
            "calibration_diagnostics": ssvi["diagnostics"],
            "independent_reference": ssvi_reference,
        },
        "heston": {
            "insample": _float_metrics(heston, INSAMPLE_METRICS),
            "oos": _generic_oos(heston_oos_surface),
            "promotion_status": heston["diagnostics"]["promotion_status"],
            "calibration_diagnostics": heston["diagnostics"],
        },
        "tenor_flat_bs": {
            "insample": _float_metrics(bs.metrics, INSAMPLE_METRICS),
            "oos": _generic_oos(bs_oos_surface),
            "promotion_status": "baseline",
        },
    }
    winners = {}
    for metric in INSAMPLE_METRICS:
        winners[f"insample_{metric}"] = min(
            models,
            key=lambda model: float(models[model]["insample"][metric]),
        )
    for metric in OOS_METRICS:
        winners[f"oos_{metric}"] = min(
            models,
            key=lambda model: float(models[model]["oos"][metric]),
        )
    payload: Dict[str, object] = {
        "trade_date": trade_date,
        "next_trade_date": next_date,
        "insample_surface_rows": int(len(today)),
        "oos_surface_rows": int(len(next_surface)),
        "models": models,
        "metric_winners": winners,
    }
    if label is not None:
        payload["label"] = label
    if regime is not None:
        payload["regime"] = regime
    if include_hedge:
        payload["hedge_diagnostics"] = _hedge_diagnostics(
            today,
            next_surface,
            heston["params"],
        )
    return payload


def _aggregate(per_date: list[Dict[str, object]]) -> Dict[str, object]:
    model_names = ("ssvi", "heston", "tenor_flat_bs")
    medians: Dict[str, Dict[str, Dict[str, float]]] = {}
    for model in model_names:
        medians[model] = {"insample": {}, "oos": {}}
        for metric in INSAMPLE_METRICS:
            medians[model]["insample"][metric] = float(
                np.median(
                    [
                        item["models"][model]["insample"][metric]
                        for item in per_date
                    ]
                )
            )
        for metric in OOS_METRICS:
            medians[model]["oos"][metric] = float(
                np.median(
                    [item["models"][model]["oos"][metric] for item in per_date]
                )
            )
    win_counts = {model: 0 for model in model_names}
    for item in per_date:
        for winner in item["metric_winners"].values():
            win_counts[str(winner)] += 1
    return {
        "date_median_metrics": medians,
        "metric_win_counts": win_counts,
        "metric_comparison_count": len(per_date)
        * (len(INSAMPLE_METRICS) + len(OOS_METRICS)),
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
        _date_result(run_root, trade_date, next_date)
        for trade_date, next_date in PREDECLARED_PAIRS
    ]
    all_ssvi_valid = all(
        item["models"]["ssvi"]["promotion_status"] == "eligible"
        and item["models"]["ssvi"]["independent_reference"]["status"] == "valid"
        for item in per_date
    )
    payload = {
        "schema_version": 1,
        "status": "development_valid" if all_ssvi_valid else "diagnostic_only",
        "claim_scope": "fixed_two_date_development_benchmark_not_superiority",
        "input_run_id": run_root.name,
        "data_policy": "aggregate_only_no_option_rows_or_parameters",
        "predeclared_date_pairs": [list(pair) for pair in PREDECLARED_PAIRS],
        "date_count": len(per_date),
        "ssvi_all_arbitrage_and_reference_gates_pass": all_ssvi_valid,
        "per_date": per_date,
        "aggregate": _aggregate(per_date),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

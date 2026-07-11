#!/usr/bin/env python3
"""Audit fitted Heston prices and deltas against independent QuantLib output.

The input run may contain licensed aggregate option surfaces.  This command
writes only date-level and panel-level error summaries: no option rows, fitted
parameters, strikes, spots, or source paths are copied into the receipt.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Mapping

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wrds_pipeline.calibrate_heston import (  # noqa: E402
    REFERENCE_LAGUERRE_SCALE,
    REFERENCE_QUADRATURE_POINTS,
    heston_call_price,
)
from wrds_pipeline.delta_hedge_pnl import heston_delta_diagnostic  # noqa: E402
from wrds_pipeline.heston_reference import (  # noqa: E402
    quantlib_heston_call_price,
    quantlib_heston_delta,
)


def _percentiles(values: Iterable[float]) -> Dict[str, float | int | None]:
    finite = np.asarray(
        [float(value) for value in values if math.isfinite(float(value))],
        dtype=float,
    )
    if finite.size == 0:
        return {"count": 0, "median": None, "p95": None, "max": None}
    return {
        "count": int(finite.size),
        "median": float(np.median(finite)),
        "p95": float(np.percentile(finite, 95.0)),
        "max": float(np.max(finite)),
    }


def _params(payload: Mapping[str, object]) -> Dict[str, float]:
    raw = payload.get("params")
    if not isinstance(raw, Mapping):
        raise ValueError("fit receipt has no parameter mapping")
    names = ("kappa", "theta", "sigma", "rho", "v0")
    params = {name: float(raw[name]) for name in names}
    if not all(math.isfinite(value) for value in params.values()):
        raise ValueError("fit receipt contains non-finite parameters")
    return params


def _audit_date(fit_path: Path) -> tuple[Dict[str, object], Dict[str, list[float]]]:
    fit_payload = json.loads(fit_path.read_text())
    params = _params(fit_payload)
    trade_date = str(fit_payload.get("trade_date") or fit_path.parent.name)
    surface_path = fit_path.parent / f"spx_{trade_date}_surface.csv"
    if not surface_path.exists():
        raise FileNotFoundError("aggregate surface is missing beside fit receipt")
    surface = pd.read_csv(surface_path)

    price_errors: list[float] = []
    price_errors_spot_bps: list[float] = []
    delta_errors: list[float] = []
    reference_delta_stability: list[float] = []
    repo_invalid_reasons: Counter[str] = Counter()
    reference_invalid_reasons: Counter[str] = Counter()
    repo_invalid_rows = 0
    reference_invalid_rows = 0
    evaluated = 0

    for _, row in surface.iterrows():
        inputs = {
            "spot": float(row["spot"]),
            "strike": float(row["strike"]),
            "rate": float(row["rate"]),
            "div": float(row["dividend"]),
            "T": float(row["ttm_years"]),
        }
        evaluated += 1
        try:
            repo_price = heston_call_price(
                **inputs,
                params=tuple(params[name] for name in ("kappa", "theta", "sigma", "rho", "v0")),
                n_points=REFERENCE_QUADRATURE_POINTS,
                laguerre_scale=REFERENCE_LAGUERRE_SCALE,
            )
            reference_price = quantlib_heston_call_price(
                **inputs,
                params=params,
            )
            price_error = abs(repo_price - reference_price)
            price_errors.append(price_error)
            price_errors_spot_bps.append(price_error / inputs["spot"] * 10_000.0)

            repo_delta = heston_delta_diagnostic(
                **inputs,
                params=params,
            )
            if not repo_delta.valid:
                repo_invalid_rows += 1
                repo_invalid_reasons.update(repo_delta.invalid_reasons)
                continue
            reference_delta = quantlib_heston_delta(
                **inputs,
                params=params,
            )
            if (
                not math.isfinite(reference_delta.value)
                or reference_delta.value < 0.0
                or reference_delta.value > reference_delta.upper_bound
            ):
                reference_invalid_rows += 1
                reference_invalid_reasons["no_arbitrage_or_nonfinite"] += 1
                continue
            delta_errors.append(abs(repo_delta.candidate - reference_delta.value))
            reference_delta_stability.append(reference_delta.bump_stability_abs)
        except Exception as exc:  # aggregate exception class only
            repo_invalid_rows += 1
            repo_invalid_reasons[type(exc).__name__] += 1

    summary: Dict[str, object] = {
        "trade_date": trade_date,
        "evaluated_surface_rows": evaluated,
        "repository_invalid_delta_rows": repo_invalid_rows,
        "repository_invalid_reason_counts": dict(sorted(repo_invalid_reasons.items())),
        "reference_invalid_delta_rows": reference_invalid_rows,
        "reference_invalid_reason_counts": dict(
            sorted(reference_invalid_reasons.items())
        ),
        "price_abs_error": _percentiles(price_errors),
        "price_abs_error_spot_bps": _percentiles(price_errors_spot_bps),
        "delta_abs_error": _percentiles(delta_errors),
        "reference_delta_bump_stability_abs": _percentiles(
            reference_delta_stability
        ),
    }
    raw = {
        "price_abs_error": price_errors,
        "price_abs_error_spot_bps": price_errors_spot_bps,
        "delta_abs_error": delta_errors,
        "reference_delta_bump_stability_abs": reference_delta_stability,
    }
    return summary, raw


def audit(run_root: Path) -> Dict[str, object]:
    fit_paths = sorted((run_root / "per_date").glob("*/heston_fit.json"))
    if not fit_paths:
        raise FileNotFoundError("no per-date Heston fit receipts found")

    per_date = []
    panel_values: Dict[str, list[float]] = {
        "price_abs_error": [],
        "price_abs_error_spot_bps": [],
        "delta_abs_error": [],
        "reference_delta_bump_stability_abs": [],
    }
    total_rows = 0
    repo_invalid = 0
    reference_invalid = 0
    for fit_path in fit_paths:
        summary, raw = _audit_date(fit_path)
        per_date.append(summary)
        total_rows += int(summary["evaluated_surface_rows"])
        repo_invalid += int(summary["repository_invalid_delta_rows"])
        reference_invalid += int(summary["reference_invalid_delta_rows"])
        for name, values in raw.items():
            panel_values[name].extend(values)

    return {
        "schema_version": 1,
        "status": "valid" if repo_invalid == 0 and reference_invalid == 0 else "invalid",
        "input_run_id": run_root.name,
        "data_policy": "aggregate_only_no_option_rows_or_parameters",
        "reference_engine": "QuantLib AnalyticHestonEngine order 192",
        "reference_maturity_convention": (
            "Actual/365 prices interpolated between adjacent integer-day maturities"
        ),
        "repository_quadrature": {
            "points": REFERENCE_QUADRATURE_POINTS,
            "laguerre_scale": REFERENCE_LAGUERRE_SCALE,
            "price_output_clipped": False,
        },
        "date_count": len(per_date),
        "evaluated_surface_rows": total_rows,
        "repository_invalid_delta_rows": repo_invalid,
        "reference_invalid_delta_rows": reference_invalid,
        "price_abs_error": _percentiles(panel_values["price_abs_error"]),
        "price_abs_error_spot_bps": _percentiles(
            panel_values["price_abs_error_spot_bps"]
        ),
        "delta_abs_error": _percentiles(panel_values["delta_abs_error"]),
        "reference_delta_bump_stability_abs": _percentiles(
            panel_values["reference_delta_bump_stability_abs"]
        ),
        "per_date": per_date,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = audit(args.run_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

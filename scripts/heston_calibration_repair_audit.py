#!/usr/bin/env python3
"""Recalibrate selected real-panel dates and emit an aggregate-only receipt."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wrds_pipeline.calibrate_heston import (  # noqa: E402
    CalibrationConfig,
    calibrate,
)

METRICS = (
    "iv_rmse_volpts_vega_wt",
    "iv_mae_volpts_vega_wt",
    "iv_p90_bps",
    "price_rmse_ticks",
)


def _change_percent(old: float, new: float) -> float | None:
    if not math.isfinite(old) or old == 0.0:
        return None
    return float((new - old) / abs(old) * 100.0)


def _audit_date(run_root: Path, trade_date: str, max_evals: int) -> Dict[str, object]:
    date_root = run_root / "per_date" / trade_date
    old_payload = json.loads((date_root / "heston_fit.json").read_text())
    surface = pd.read_csv(date_root / f"spx_{trade_date}_surface.csv")
    result = calibrate(
        surface,
        CalibrationConfig(
            fast=False,
            max_evals=max_evals,
            bootstrap_samples=0,
            rng_seed=19,
            multistart=True,
        ),
    )
    old_metrics = {name: float(old_payload[name]) for name in METRICS}
    new_metrics = {name: float(result[name]) for name in METRICS}
    diagnostics = dict(result["diagnostics"])
    return {
        "trade_date": trade_date,
        "surface_row_count": int(len(surface)),
        "old_metrics": old_metrics,
        "repaired_metrics": new_metrics,
        "change_percent": {
            name: _change_percent(old_metrics[name], new_metrics[name])
            for name in METRICS
        },
        "calibration_diagnostics": diagnostics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--dates", required=True, nargs="+")
    parser.add_argument("--max-evals", type=int, default=160)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_evals <= 0:
        raise ValueError("max-evals must be positive")
    run_root = args.run_root.resolve()
    per_date = [
        _audit_date(run_root, trade_date, args.max_evals)
        for trade_date in args.dates
    ]
    payload = {
        "schema_version": 1,
        "status": (
            "eligible"
            if all(
                item["calibration_diagnostics"]["promotion_eligible"]
                for item in per_date
            )
            else "diagnostic_only"
        ),
        "input_run_id": run_root.name,
        "data_policy": "aggregate_only_no_option_rows_or_parameters",
        "date_count": len(per_date),
        "eligible_date_count": sum(
            bool(item["calibration_diagnostics"]["promotion_eligible"])
            for item in per_date
        ),
        "per_date": per_date,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

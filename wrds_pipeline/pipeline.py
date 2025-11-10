#!/usr/bin/env python3
"""Run the WRDS sample pipeline end-to-end."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from manifest_utils import ARTIFACTS_ROOT, update_run

from wrds_pipeline import ingest_sppx_surface
from wrds_pipeline import calibrate_heston
from wrds_pipeline import oos_pricing
from wrds_pipeline import delta_hedge_pnl


def _wrds_env_ready() -> bool:
    return (
        os.environ.get("WRDS_ENABLED") == "1"
        and bool(os.environ.get("WRDS_USERNAME"))
        and bool(os.environ.get("WRDS_PASSWORD"))
    )


def run(use_sample: bool = False) -> None:
    out_dir = ARTIFACTS_ROOT / "wrds"
    out_dir.mkdir(parents=True, exist_ok=True)

    surface_raw, source = ingest_sppx_surface.load_surface(force_sample=use_sample)
    aggregated = ingest_sppx_surface.aggregate_surface(surface_raw)
    surface_path = out_dir / "spx_surface_sample.csv"
    ingest_sppx_surface.write_surface(surface_path, aggregated)

    summary = calibrate_heston.calibrate(aggregated)
    calib_path = out_dir / "heston_calibration_summary.csv"
    calibrate_heston.write_summary(calib_path, summary)

    priced = oos_pricing.evaluate(aggregated, summary["atm_iv"])
    oos_csv = out_dir / "oos_pricing.csv"
    oos_summary = out_dir / "oos_pricing_summary.csv"
    oos_pricing.write_outputs(oos_csv, oos_summary, priced, oos_pricing.summarize(priced))

    delta_path = out_dir / "delta_hedge_pnl.csv"
    delta_hedge_pnl.write_outputs(delta_path, delta_hedge_pnl.simulate())

    update_run(
        "wrds_pipeline",
        {
            "source": source,
            "surface": str(surface_path),
            "calibration": str(calib_path),
            "oos_pricing": str(oos_csv),
            "oos_summary": str(oos_summary),
            "delta_hedge": str(delta_path),
            "atm_iv": summary["atm_iv"],
            "rmse_iv": summary["rmse_iv"],
            "rows": len(aggregated),
            "use_sample": use_sample,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        append=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-sample", action="store_true", help="Force sample data")
    args = ap.parse_args()
    use_sample = args.use_sample or not _wrds_env_ready()
    if use_sample:
        os.environ.pop("WRDS_ENABLED", None)
    run(use_sample=use_sample)


if __name__ == "__main__":  # pragma: no cover
    main()

#!/usr/bin/env python3
"""
Run Heston calibration across multiple normalized option surfaces.

For each input CSV (matching `scripts/data/schema.md`) the script emits the same
artifacts as `calibrate_heston.py` plus a consolidated CSV summarising the time
series of parameters.

Usage:
  ./scripts/calibrate_heston_series.py --pattern 'data/normalized/spx_*.csv'
  ./scripts/calibrate_heston_series.py --inputs data/samples/spx_20240614_sample.csv --fast
"""
from __future__ import annotations

import argparse
import glob
import shlex
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from calibrate_heston import (
    CalibrationConfig,
    calibrate_surface,
    save_calibration_outputs,
)
from manifest_utils import update_run


def resolve_inputs(inputs: Iterable[str], pattern: str, input_dir: str) -> List[Path]:
    paths: List[Path] = []
    for item in inputs:
        paths.append(Path(item))
    if not paths:
        search_pattern = pattern
        if not Path(pattern).anchor:
            search_pattern = str(Path(input_dir) / pattern)
        paths = [Path(p) for p in sorted(glob.glob(search_pattern))]
    resolved = [p for p in paths if p.exists()]
    if not resolved:
        raise FileNotFoundError(f"No input CSV files matched pattern '{pattern}'")
    return resolved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inputs",
        nargs="*",
        default=[],
        help="Explicit list of normalized CSV files",
    )
    ap.add_argument(
        "--pattern",
        default="spx_*.csv",
        help="Glob pattern (relative to --input-dir) when --inputs is empty",
    )
    ap.add_argument(
        "--input-dir",
        default="data/normalized",
        help="Directory to search when using --pattern",
    )
    ap.add_argument(
        "--output",
        default="artifacts/heston/series_params.csv",
        help="CSV collecting calibration parameters",
    )
    ap.add_argument(
        "--artifacts-dir",
        default="artifacts/heston",
        help="Directory for per-date artifacts",
    )
    ap.add_argument("--metric", choices=["price", "vol"], default="price")
    ap.add_argument("--fast", action="store_true", help="FAST mode for CI")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--retries", type=int, default=4)
    args = ap.parse_args()

    inputs = resolve_inputs(args.inputs, args.pattern, args.input_dir)
    output_dir = Path(args.artifacts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for idx, path in enumerate(inputs):
        print(f"[{idx+1}/{len(inputs)}] Calibrating {path}")
        df = pd.read_csv(path)
        config = CalibrationConfig(
            fast=args.fast,
            metric=args.metric,
            seed=args.seed + idx,
            retries=args.retries,
        )
        metrics, surface = calibrate_surface(df, config)
        metrics["input"] = str(path)
        outputs = save_calibration_outputs(surface, metrics, output_dir, args.fast)
        params = metrics["params"]
        rows.append(
            {
                "date": surface["date"].iloc[0].isoformat(),
                "input_csv": str(path),
                "fast_mode": bool(args.fast),
                "metric": args.metric,
                "kappa": params["kappa"],
                "theta": params["theta"],
                "sigma": params["sigma"],
                "rho": params["rho"],
                "v0": params["v0"],
                "rmse_price": metrics["rmse_price"],
                "rmse_vol": metrics["rmse_vol"],
                "feller": metrics["feller"],
                "n_obs": metrics["n_obs"],
                "cost": metrics["cost"],
                "nit": metrics["nit"],
                "params_json": str(outputs["params_path"]),
                "figure_png": str(outputs["figure_path"]),
                "table_csv": str(outputs["table_path"]),
            }
        )

    df = pd.DataFrame(rows).sort_values("date")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote series parameters -> {out_path}")

    command = shlex.join([sys.executable] + sys.argv)
    manifest_entry = {
        "command": command,
        "fast": bool(args.fast),
        "metric": args.metric,
        "seed": args.seed,
        "retries": args.retries,
        "inputs": [str(p) for p in inputs],
        "artifacts_dir": str(output_dir),
        "series_csv": str(out_path),
        "num_dates": int(len(rows)),
        "dates": df["date"].tolist(),
        "entries": rows,
    }
    update_run("heston_series", manifest_entry)


if __name__ == "__main__":
    main()

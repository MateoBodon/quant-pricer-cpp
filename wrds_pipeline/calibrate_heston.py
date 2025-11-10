#!/usr/bin/env python3
"""Heuristic Heston calibration using aggregated surface data."""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from manifest_utils import update_run


def calibrate(surface: pd.DataFrame) -> Dict[str, float]:
    atm = surface.iloc[(surface["moneyness"].sub(1.0).abs()).argsort()].head(1)
    atm_iv = float(atm["mid_iv"].iloc[0])
    theta = atm_iv ** 2
    v0 = theta
    kappa = 1.5
    sigma = 0.5
    rho = -0.5
    rmse = math.sqrt(float(((surface["mid_iv"] - atm_iv) ** 2).mean()))
    return {
        "kappa": kappa,
        "theta": theta,
        "sigma": sigma,
        "rho": rho,
        "v0": v0,
        "atm_iv": atm_iv,
        "rmse_iv": rmse,
    }


def write_summary(out_path: Path, summary: Dict[str, float]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(out_path, index=False)


def record_manifest(out_csv: Path, summary: Dict[str, float]) -> None:
    payload = {
        "path": str(out_csv),
        "kappa": summary["kappa"],
        "theta": summary["theta"],
        "sigma": summary["sigma"],
        "rho": summary["rho"],
        "v0": summary["v0"],
        "rmse_iv": summary["rmse_iv"],
    }
    update_run("wrds_heston", payload, append=True)


if __name__ == "__main__":  # pragma: no cover
    sample = pd.read_csv("docs/artifacts/wrds/spx_surface_sample.csv")
    summary = calibrate(sample)
    out_csv = Path("docs/artifacts/wrds/heston_calibration_summary.csv")
    write_summary(out_csv, summary)
    record_manifest(out_csv, summary)
    print(f"Wrote {out_csv}")

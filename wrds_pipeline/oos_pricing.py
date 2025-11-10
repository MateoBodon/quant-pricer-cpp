#!/usr/bin/env python3
"""Simple out-of-sample pricing diagnostic."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def evaluate(surface: pd.DataFrame, atm_iv: float) -> pd.DataFrame:
    df = surface.copy()
    df["bs_price"] = df["mid_iv"].apply(lambda iv: max(0.0, iv - atm_iv))
    df["abs_diff"] = (df["mid_iv"] - atm_iv).abs()
    return df[["tenor_bucket", "moneyness", "mid_iv", "bs_price", "abs_diff"]]


def summarize(df: pd.DataFrame) -> Dict[str, float]:
    return {
        "mae": float(df["abs_diff"].mean()),
        "max_err": float(df["abs_diff"].max()),
    }


def write_outputs(out_csv: Path, out_summary: Path, df: pd.DataFrame, metrics: Dict[str, float]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    pd.DataFrame([metrics]).to_csv(out_summary, index=False)


if __name__ == "__main__":  # pragma: no cover
    surface = pd.read_csv("docs/artifacts/wrds/spx_surface_sample.csv")
    summary = pd.read_csv("docs/artifacts/wrds/heston_calibration_summary.csv")
    atm_iv = float(summary["atm_iv"].iloc[0])
    priced = evaluate(surface, atm_iv)
    metrics = summarize(priced)
    write_outputs(
        Path("docs/artifacts/wrds/oos_pricing.csv"),
        Path("docs/artifacts/wrds/oos_pricing_summary.csv"),
        priced,
        metrics,
    )
    print("Wrote OOS pricing diagnostics")

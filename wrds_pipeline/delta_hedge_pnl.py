#!/usr/bin/env python3
"""Toy delta-hedge PnL generator (synthetic)."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd


def simulate(days: int = 10, seed: int = 42) -> pd.DataFrame:
    rng = pd.Series(range(days), dtype=float)
    pnl = 0.1 * (rng - rng.mean())  # deterministic ramp for reproducibility
    start = datetime(2024, 6, 14)
    dates: List[str] = [(start + timedelta(days=int(i))).strftime("%Y-%m-%d") for i in rng]
    return pd.DataFrame({"date": dates, "pnl": pnl})


def write_outputs(out_path: Path, df: pd.DataFrame) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


if __name__ == "__main__":  # pragma: no cover
    out = Path("docs/artifacts/wrds/delta_hedge_pnl.csv")
    write_outputs(out, simulate())
    print(f"Wrote {out}")

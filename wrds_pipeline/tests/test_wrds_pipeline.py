#!/usr/bin/env python3
"""MARKET test wrapper for the WRDS pipeline."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import math
from pathlib import Path
from typing import List

import pandas as pd

SKIP_CODE = 77


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _has_wrds_env() -> bool:
    return (
        os.environ.get("WRDS_ENABLED") == "1"
        and bool(os.environ.get("WRDS_USERNAME"))
        and bool(os.environ.get("WRDS_PASSWORD"))
    )


def _expected_artifacts(base: Path) -> list[Path]:
    return [
        base / "wrds_agg_pricing.csv",
        base / "wrds_agg_oos.csv",
        base / "wrds_agg_pnl.csv",
        base / "wrds_multi_date_summary.png",
        base / "wrds_bs_heston_comparison.csv",
    ]


def _write_dateset(path: Path) -> Path:
    payload = {
        "panel_id": "wrds_test_smoke",
        "dates": [
            {
                "trade_date": "2020-03-16",
                "next_trade_date": "2020-03-17",
                "label": "smoke-stress",
                "regime": "stress",
            },
            {
                "trade_date": "2024-06-14",
                "next_trade_date": "2024-06-17",
                "label": "smoke-calm",
                "regime": "calm",
            },
        ]
    }
    path.write_text(json.dumps(payload))
    return path


def _baseline_sigma() -> pd.Series:
    """Reference Δ-hedge σ from bundled sample comparison (regression harness)."""
    repo_root = _root()
    base_path = repo_root / "docs/artifacts/wrds/wrds_bs_heston_comparison.csv"
    if not base_path.exists():
        return pd.Series(dtype=float)
    base = pd.read_csv(base_path)
    return base.set_index("tenor_bucket")["heston_pnl_sigma"]


def _assert_tolerances(wrds_root: Path, dates: List[str]) -> None:
    comp_path = wrds_root / "wrds_bs_heston_comparison.csv"
    comp = pd.read_csv(comp_path)
    assert not comp.empty, "comparison CSV is empty"
    assert comp["heston_iv_rmse_volpts"].dropna().between(0.0, 1.0).all()
    assert comp["bs_iv_rmse_volpts"].dropna().between(0.0, 1.0).all()
    assert comp["heston_price_rmse_ticks"].dropna().between(0.0, 4000.0).all()
    assert comp["bs_price_rmse_ticks"].dropna().between(0.0, 4000.0).all()
    assert comp["heston_oos_iv_mae_bps"].dropna().between(0.0, 3000.0).all()
    assert comp["heston_oos_price_mae_ticks"].dropna().between(0.0, 4000.0).all()

    baseline_sigma = _baseline_sigma()
    if not baseline_sigma.empty:
        sigma = comp.set_index("tenor_bucket")["heston_pnl_sigma"].dropna()
        for bucket, val in sigma.items():
            base = baseline_sigma.get(bucket)
            valid_base = base is not None and not math.isnan(base) and base > 0
            lo = 0.2 * base if valid_base else 0.0
            hi = 5.0 * base if valid_base else 2000.0
            assert lo <= val <= hi, f"{bucket} hedge σ {val} outside [{lo}, {hi}]"

    pricing = pd.read_csv(wrds_root / "wrds_agg_pricing.csv")
    filtered = pricing[pricing["trade_date"].isin(dates)]
    assert not filtered.empty, "pricing aggregate missing expected dates"
    assert filtered["iv_rmse_volpts_vega_wt"].dropna().between(0.0, 1.0).all()
    assert filtered["price_rmse_ticks"].dropna().between(0.0, 4000.0).all()


def main() -> None:
    repo_root = _root()
    if not _has_wrds_env():
        print(
            "SKIP: WRDS pipeline disabled (set WRDS_ENABLED=1 with WRDS_USERNAME/WRDS_PASSWORD)."
        )
        raise SystemExit(SKIP_CODE)

    env = os.environ.copy()
    dates = ["2020-03-16", "2024-06-14"]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        dateset = _write_dateset(tmp_path / "wrds_test_dates.json")
        out_root = tmp_path / "wrds_artifacts"
        cmd = [
            sys.executable,
            "-m",
            "wrds_pipeline.pipeline",
            "--dateset",
            str(dateset),
            "--fast",
            "--output-root",
            str(out_root),
        ]
        subprocess.run(cmd, check=True, cwd=repo_root, env=env)
        env["WRDS_CACHE_ROOT"] = str(out_root)
        missing = [path for path in _expected_artifacts(out_root) if not path.exists()]
        if missing:
            raise SystemExit(
                f"Missing WRDS artifacts: {', '.join(str(path) for path in missing)}"
            )
        _assert_tolerances(out_root, dates)
    print("WRDS pipeline artifacts ready.")


if __name__ == "__main__":
    main()

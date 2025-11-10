#!/usr/bin/env python3
"""OptionMetrics SPX surface ingestion helper (WRDS opt-in)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import pandas as pd

SAMPLE_PATH = Path(__file__).resolve().parent / "sample_data" / "spx_options_sample.csv"


def _has_wrds_credentials() -> bool:
    return bool(os.environ.get("WRDS_USERNAME")) and bool(os.environ.get("WRDS_PASSWORD"))


def _fetch_from_wrds(symbol: str, trade_date: str) -> pd.DataFrame:
    """Fetch raw OptionMetrics rows from WRDS (requires credentials)."""
    username = os.environ.get("WRDS_USERNAME")
    password = os.environ.get("WRDS_PASSWORD")
    if not username or not password:
        raise RuntimeError("WRDS credentials not set in the environment")
    try:
        import pandas as pd  # noqa: F401
        import psycopg2
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("psycopg2 is required for WRDS access") from exc

    conn = psycopg2.connect(
        host="wrds-pgdata.wharton.upenn.edu",
        port=9737,
        database="wrds",
        user=username,
        password=password,
    )
    query = """
        select date, secid, exdate, strike_price/1000.0 as strike,
               best_bid, best_offer, impl_volatility,
               days_to_expiration
        from optionm.opprcd
        where symbol = %s AND date = %s AND cp_flag = 'C'
          AND best_bid is not null AND best_offer is not null
        limit 5000
    """
    df = pd.read_sql(query, conn, params=[symbol, trade_date])
    conn.close()
    df["spot"] = df["best_bid"] * 0 + 4400.0  # placeholder spot until integrated with equities
    df["call_put"] = "C"
    df["mid_iv"] = df["impl_volatility"].clip(lower=0.01)
    df["option_mid"] = 0.5 * (df["best_bid"] + df["best_offer"])
    return df[[
        "date",
        "spot",
        "strike",
        "days_to_expiration",
        "call_put",
        "mid_iv",
        "option_mid",
    ]].rename(columns={"date": "trade_date"})


def load_surface(symbol: str = "SPX", trade_date: str = "2024-06-14", force_sample: bool = False) -> Tuple[pd.DataFrame, str]:
    """Return a DataFrame of option rows plus the data source label."""
    use_wrds = os.environ.get("WRDS_ENABLED") == "1" and not force_sample and _has_wrds_credentials()
    if use_wrds:
        try:
            raw = _fetch_from_wrds(symbol, trade_date)
            return raw, "wrds"
        except Exception as exc:  # pragma: no cover - offline fallback
            print(f"[wrds_pipeline] WRDS fetch failed ({exc}); falling back to sample data")
    raw = pd.read_csv(SAMPLE_PATH)
    return raw, "sample"


def aggregate_surface(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to tenor/moneyness buckets."""
    df = df.copy()
    df["moneyness"] = df["strike"] / df["spot"]
    df["tenor_bucket"] = pd.cut(df["days_to_expiration"], bins=[0, 45, 75, 120], labels=["30d", "60d", "90d"], include_lowest=True)
    grouped = (
        df.groupby(["tenor_bucket", "moneyness"], dropna=True, observed=False)
        .agg(mid_iv=("mid_iv", "mean"), quotes=("mid_iv", "count"))
        .reset_index()
        .dropna(subset=["tenor_bucket"])
    )
    return grouped


def write_surface(out_path: Path, df: pd.DataFrame) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


if __name__ == "__main__":  # pragma: no cover
    surface, source = load_surface()
    aggregated = aggregate_surface(surface)
    write_surface(Path("docs/artifacts/wrds/spx_surface_sample.csv"), aggregated)
    print(f"Wrote surface from {source} with {len(aggregated)} rows")

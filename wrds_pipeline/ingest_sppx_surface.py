#!/usr/bin/env python3
"""OptionMetrics SPX surface ingestion helper (WRDS opt-in)."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd
from psycopg2 import errors

SAMPLE_PATH = Path(__file__).resolve().parent / "sample_data" / "spx_options_sample.csv"
SPOT_FALLBACK = 4500.0


def _has_wrds_credentials() -> bool:
    return bool(os.environ.get("WRDS_USERNAME")) and bool(os.environ.get("WRDS_PASSWORD"))


def _table_for_trade_date(trade_date: str) -> str:
    year = pd.to_datetime(trade_date).year
    return f"opprcd{year}"


def _resolve_secid(conn, ticker: str, trade_date: str) -> float:
    cur = conn.cursor()
    cur.execute(
        """
        select secid
        from optionm.secnmd
        where ticker = %s AND effect_date <= %s
        order by effect_date desc
        limit 1
        """,
        (ticker, trade_date),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        raise RuntimeError(f"WRDS missing secid for ticker {ticker}")
    return row[0]


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
    table = _table_for_trade_date(trade_date)
    secid = _resolve_secid(conn, symbol, trade_date)
    query = f"""
        select date, secid, exdate, strike_price/1000.0 as strike,
               best_bid, best_offer, impl_volatility,
               forward_price
        from optionm.{table}
        where secid = %s AND date = %s AND cp_flag = 'C'
          AND best_bid is not null AND best_offer is not null
        limit 5000
    """
    try:
        df = pd.read_sql(query, conn, params=[secid, trade_date])
    except errors.UndefinedTable as exc:
        conn.close()
        raise RuntimeError(f"WRDS table optionm.{table} is unavailable") from exc
    finally:
        conn.close()
    if df.empty:
        raise RuntimeError(f"WRDS returned no rows for {symbol} on {trade_date}")
    df["date"] = pd.to_datetime(df["date"])
    df["exdate"] = pd.to_datetime(df["exdate"])
    df["days_to_expiration"] = (df["exdate"] - df["date"]).dt.days
    df["spot"] = df["forward_price"].fillna(SPOT_FALLBACK)
    df.loc[df["spot"] <= 0, "spot"] = SPOT_FALLBACK
    df["call_put"] = "C"
    df["mid_iv"] = df["impl_volatility"].clip(lower=0.01)
    df = df.dropna(subset=["mid_iv"])
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
    df = df[df["days_to_expiration"] > 0]
    df["moneyness"] = df["strike"] / df["spot"]
    df = df[df["moneyness"].between(0.5, 1.5)]
    df["tenor_bucket"] = pd.cut(df["days_to_expiration"], bins=[0, 45, 75, 120], labels=["30d", "60d", "90d"], include_lowest=True)
    df = df.dropna(subset=["mid_iv", "moneyness", "tenor_bucket"])
    grouped = (
        df.groupby(["tenor_bucket", "moneyness"], dropna=True, observed=False)
        .agg(mid_iv=("mid_iv", "mean"), quotes=("mid_iv", "count"))
        .reset_index()
        .dropna(subset=["tenor_bucket"])
    )
    grouped = grouped[grouped["quotes"] > 0]
    return grouped


def write_surface(out_path: Path, df: pd.DataFrame) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


if __name__ == "__main__":  # pragma: no cover
    surface, source = load_surface()
    aggregated = aggregate_surface(surface)
    write_surface(Path("docs/artifacts/wrds/spx_surface_sample.csv"), aggregated)
    print(f"Wrote surface from {source} with {len(aggregated)} rows")

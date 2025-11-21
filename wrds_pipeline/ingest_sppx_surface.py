#!/usr/bin/env python3
"""OptionMetrics SPX ingestion + aggregation helpers."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .bs_utils import bs_vega, implied_vol_from_price

SAMPLE_PATH = Path(__file__).resolve().parent / "sample_data" / "spx_options_sample.csv"
SPOT_FALLBACK = 4500.0


def _has_wrds_credentials() -> bool:
    return (
        os.environ.get("WRDS_ENABLED") == "1"
        and bool(os.environ.get("WRDS_USERNAME"))
        and bool(os.environ.get("WRDS_PASSWORD"))
    )


def _table_for_trade_date(trade_date: str) -> str:
    year = pd.to_datetime(trade_date).year
    return f"opprcd{year}"


def _secprd_table(trade_date: str) -> str:
    year = pd.to_datetime(trade_date).year
    return f"secprd{year}"


def _resolve_secid(conn, ticker: str, trade_date: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT secid
        FROM optionm.secnmd
        WHERE ticker = %s AND effect_date <= %s
        ORDER BY effect_date DESC
        LIMIT 1
        """,
        (ticker, trade_date),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        raise RuntimeError(f"WRDS missing secid for ticker {ticker}")
    return int(row[0])


def _fetch_from_wrds(symbol: str, trade_date: str) -> pd.DataFrame:
    try:
        import psycopg2
        from psycopg2 import errors
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg2 is required for WRDS access") from exc

    username = os.environ["WRDS_USERNAME"]
    password = os.environ["WRDS_PASSWORD"]
    conn = psycopg2.connect(
        host="wrds-pgdata.wharton.upenn.edu",
        port=9737,
        database="wrds",
        user=username,
        password=password,
    )
    table = _table_for_trade_date(trade_date)
    secid = _resolve_secid(conn, symbol, trade_date)
    base_query = f"""
        SELECT
            date,
            exdate,
            cp_flag,
            strike_price / 1000.0 AS strike,
            best_bid,
            best_offer,
            forward_price
        FROM optionm.{table}
        WHERE secid = %s
          AND date = %s
          AND cp_flag = 'C'
          AND best_bid IS NOT NULL
          AND best_offer IS NOT NULL
          AND best_bid > 0
          AND best_offer > best_bid
        LIMIT 6000
    """
    fallback_query = base_query
    try:
        df = pd.read_sql(base_query, conn, params=[secid, trade_date])
        spot_query = f"""
            SELECT close
            FROM optionm.{_secprd_table(trade_date)}
            WHERE secid = %s AND date = %s
            LIMIT 1
        """
        spot_df = pd.read_sql(spot_query, conn, params=[secid, trade_date])
        spot_val = float(spot_df["close"].iloc[0]) if not spot_df.empty else SPOT_FALLBACK
        df["spot"] = spot_val
    except errors.UndefinedTable as exc:  # pragma: no cover
        conn.close()
        raise RuntimeError(f"WRDS table optionm.{table} unavailable") from exc
    except Exception as exc:
        conn.close()
        raise
    finally:
        conn.close()
    if "rate" not in df.columns:
        df["rate"] = 0.015
    if "divyield" not in df.columns:
        df["divyield"] = 0.01
    return df


def _load_sample(symbol: str, trade_date: str) -> pd.DataFrame:
    df = pd.read_csv(SAMPLE_PATH, parse_dates=["trade_date", "exdate"])
    df = df[df["trade_date"] == pd.to_datetime(trade_date)]
    if df.empty:
        raise RuntimeError(f"Sample data missing trade date {trade_date}")
    df = df.copy()
    df["cp_flag"] = "C"
    df["strike"] = df["strike_price"] / 1.0
    df["rate"] = df.get("rate", 0.015)
    df["divyield"] = df.get("dividend", 0.01)
    df["underlying_bid"] = df.get("spot", SPOT_FALLBACK)
    df["underlying_ask"] = df.get("spot", SPOT_FALLBACK)
    return df[
        [
            "trade_date",
            "exdate",
            "cp_flag",
            "strike",
            "best_bid",
            "best_offer",
            "forward_price",
            "underlying_bid",
            "underlying_ask",
            "rate",
            "divyield",
        ]
    ]


def load_surface(
    symbol: str, trade_date: str, force_sample: bool = False
) -> Tuple[pd.DataFrame, str]:
    trade_date = pd.to_datetime(trade_date).date()
    if not force_sample and _has_wrds_credentials():
        try:
            raw = _fetch_from_wrds(symbol, str(trade_date))
            raw["trade_date"] = pd.to_datetime(raw["date"])
            raw.drop(columns=["date"], inplace=True)
            return raw, "wrds"
        except Exception as exc:  # pragma: no cover
            print(
                f"[wrds_pipeline] WRDS fetch failed ({exc}); falling back to sample data"
            )
    sample = _load_sample(symbol, str(trade_date))
    return sample, "sample"


def _prepare_quotes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["exdate"] = pd.to_datetime(df["exdate"])
    df["days_to_expiration"] = (df["exdate"] - df["trade_date"]).dt.days
    df = df[df["days_to_expiration"] > 0]
    df["ttm_years"] = df["days_to_expiration"] / 365.0
    df["option_mid"] = 0.5 * (df["best_bid"] + df["best_offer"])
    df = df[(df["option_mid"] > 0.01)]
    if "underlying_bid" in df.columns and "underlying_ask" in df.columns:
        underlying_mid = 0.5 * (df["underlying_bid"] + df["underlying_ask"])
    else:
        underlying_mid = pd.Series(np.nan, index=df.index)
    base_spot = df["spot"] if "spot" in df.columns else pd.Series(np.nan, index=df.index)
    forward = df["forward_price"] if "forward_price" in df.columns else pd.Series(np.nan, index=df.index)
    df["spot"] = (
        base_spot.fillna(underlying_mid).fillna(forward).fillna(SPOT_FALLBACK)
    )
    df["spot"] = np.clip(df["spot"], 1000.0, 20000.0)
    df["rate"] = df.get("rate", 0.015).fillna(0.015)
    df["dividend"] = df.get("dividend", df.get("divyield", 0.01)).fillna(0.01)
    df["strike"] = df["strike"].fillna(df.get("strike_price", df["spot"]))
    df = df[df["strike"] > 0]
    df["moneyness"] = df["strike"] / df["spot"]
    df = df[df["moneyness"].between(0.6, 1.4)]

    def _compute_iv(row: pd.Series) -> float:
        return implied_vol_from_price(
            price=float(row["option_mid"]),
            spot=float(row["spot"]),
            strike=float(row["strike"]),
            rate=float(row["rate"]),
            div=float(row["dividend"]),
            T=float(row["ttm_years"]),
            option="call",
        )

    df["mid_iv"] = df.apply(_compute_iv, axis=1).clip(0.05, 3.0)
    # Discard nodes that hit the clip boundaries; they originate from noisy quotes
    # and destabilise the Heston calibration objective.
    df = df[(df["mid_iv"] > 0.051) & (df["mid_iv"] < 2.99)]
    df["vega"] = df.apply(
        lambda row: bs_vega(
            float(row["spot"]),
            float(row["strike"]),
            float(row["rate"]),
            float(row["dividend"]),
            float(row["mid_iv"]),
            float(row["ttm_years"]),
        ),
        axis=1,
    )
    df = df[df["vega"] > 1e-5]
    return df


def aggregate_surface(df: pd.DataFrame) -> pd.DataFrame:
    quotes = _prepare_quotes(df)
    if quotes.empty:
        raise RuntimeError("No valid quotes after filtering")
    bins_days = [0, 45, 75, 120, 240, 720]
    labels = ["30d", "60d", "90d", "6m", "1y"]
    quotes["tenor_bucket"] = pd.cut(
        quotes["days_to_expiration"],
        bins=bins_days,
        labels=labels,
        include_lowest=True,
    )
    quotes = quotes.dropna(subset=["tenor_bucket"])
    quotes["moneyness_bucket"] = np.round(quotes["moneyness"], 2)
    grouped = (
        quotes.groupby(
            ["tenor_bucket", "moneyness_bucket"],
            observed=True,
            as_index=True,
        )
        .agg(
            trade_date=("trade_date", "first"),
            spot=("spot", "mean"),
            strike=("strike", "mean"),
            rate=("rate", "mean"),
            dividend=("dividend", "mean"),
            ttm_years=("ttm_years", "mean"),
            days_to_expiration=("days_to_expiration", "mean"),
            mid_price=("option_mid", "mean"),
            mid_iv=("mid_iv", "mean"),
            vega=("vega", "mean"),
            quotes=("option_mid", "count"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["quotes"] >= 1]
    grouped["symbol"] = "SPX"
    grouped["moneyness"] = grouped["moneyness_bucket"]
    columns = [
        "symbol",
        "trade_date",
        "tenor_bucket",
        "moneyness",
        "ttm_years",
        "days_to_expiration",
        "spot",
        "strike",
        "rate",
        "dividend",
        "mid_price",
        "mid_iv",
        "vega",
        "quotes",
    ]
    return (
        grouped[columns]
        .sort_values(["tenor_bucket", "moneyness"])
        .reset_index(drop=True)
    )


def write_surface(out_path: Path, df: pd.DataFrame) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def has_wrds_credentials() -> bool:
    return _has_wrds_credentials()


if __name__ == "__main__":  # pragma: no cover
    data, source = load_surface("SPX", datetime.now().strftime("%Y-%m-%d"))
    agg = aggregate_surface(data)
    write_surface(Path("docs/artifacts/wrds/spx_surface_debug.csv"), agg)
    print(f"{source}: wrote {len(agg)} aggregated rows")

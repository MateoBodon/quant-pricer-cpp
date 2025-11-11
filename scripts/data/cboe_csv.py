#!/usr/bin/env python3
"""
Normalize a raw CBOE option surface export into the project standard schema.

Expected input columns (case-insensitive):
  - Quote date:        quote_date | trade_date | date
  - Expiration date:   expiration | expiration_date | expiry
  - Option type:       option_type (C/P) | cp_flag | call_put
  - Strike:            strike | strike_price
  - Implied vol:       implied_volatility | iv | imp_vol
  - Bid/Ask:           bid | bid_price, ask | ask_price
  - Underlying spot:   underlying_price | spot | underlying_bid_1545 | underlying_mid
  - Risk-free rate:    interest_rate | r (optional, defaults to 0)
  - Dividend yield:    dividend_yield | q (optional, defaults to 0)

Usage:
  ./scripts/data/cboe_csv.py --input data/raw/cboe_spx_20240614.csv

Outputs `data/normalized/<symbol_lower>_YYYYMMDD.csv` with the schema documented
in `scripts/data/schema.md`.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

COLUMN_ALIASES = {
    "quote_date": ["quote_date", "trade_date", "date"],
    "expiration": ["expiration", "expiration_date", "expiry"],
    "option_type": ["option_type", "cp_flag", "call_put"],
    "strike": ["strike", "strike_price"],
    "implied_vol": ["implied_volatility", "iv", "impl_vol", "imp_vol", "mid_iv"],
    "bid": ["bid", "bid_price"],
    "ask": ["ask", "ask_price"],
    "spot": [
        "underlying_price",
        "spot",
        "underlying_mid",
        "underlying_bid",
        "underlying_bid_1545",
        "underlying_ask_1545",
    ],
    "rate": ["interest_rate", "r", "risk_free_rate"],
    "dividend": ["dividend_yield", "q", "borrow_rate", "repo_rate"],
}

STANDARD_COLUMNS = [
    "date",
    "ttm_years",
    "strike",
    "mid_iv",
    "put_call",
    "spot",
    "r",
    "q",
    "bid",
    "ask",
]


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    lowered = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    return None


def _normalized_put_call(raw: str) -> str:
    if raw is None:
        return ""
    raw = str(raw).strip().lower()
    if raw in {"c", "call"}:
        return "call"
    if raw in {"p", "put"}:
        return "put"
    raise ValueError(f"Cannot map option type '{raw}' to put/call")


def _parse_date(value: str, fallback: Optional[str] = None) -> dt.date:
    if isinstance(value, dt.date):
        return value
    if pd.isna(value) and fallback:
        value = fallback
    if pd.isna(value):
        raise ValueError("Missing trade date")
    value = str(value).split(" ")[0]
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"]:
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date '{value}'")


def _parse_rate(series: pd.Series, default: float = 0.0) -> pd.Series:
    if series.isna().all():
        return pd.Series(default, index=series.index, dtype=float)
    values = series.astype(float).fillna(default)
    # If values look like percents (>1), scale down.
    if values.abs().max() > 1.0:
        values = values / 100.0
    return values


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Raw CBOE CSV export")
    ap.add_argument(
        "--output-dir",
        default="data/normalized",
        help="Directory for normalized CSV files",
    )
    ap.add_argument("--symbol", default="SPX", help="Underlying ticker (for naming)")
    ap.add_argument(
        "--trade-date",
        help="Override trade date (YYYY-MM-DD); inferred from file otherwise",
    )
    ap.add_argument(
        "--min-ttm-days",
        type=float,
        default=1.0,
        help="Minimum time-to-maturity in days (filter noise)",
    )
    args = ap.parse_args()

    raw_path = Path(args.input)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    df = pd.read_csv(raw_path)
    if df.empty:
        raise ValueError("Input CSV contains no rows")

    col = _find_column(df.columns, COLUMN_ALIASES["quote_date"])
    if col is None and not args.trade_date:
        raise ValueError("Trade date column missing; pass --trade-date")
    trade_date = _parse_date(df[col].iloc[0]) if col else _parse_date(args.trade_date)

    exp_col = _find_column(df.columns, COLUMN_ALIASES["expiration"])
    if exp_col is None:
        raise ValueError("Expiration column not found in input")

    strike_col = _find_column(df.columns, COLUMN_ALIASES["strike"])
    if strike_col is None:
        raise ValueError("Strike column not found in input")

    type_col = _find_column(df.columns, COLUMN_ALIASES["option_type"])
    if type_col is None:
        raise ValueError("Option type column not found in input")

    iv_col = _find_column(df.columns, COLUMN_ALIASES["implied_vol"])
    if iv_col is None:
        raise ValueError("Implied volatility column not found in input")

    bid_col = _find_column(df.columns, COLUMN_ALIASES["bid"])
    ask_col = _find_column(df.columns, COLUMN_ALIASES["ask"])
    if bid_col is None or ask_col is None:
        raise ValueError("Bid/Ask columns must be present in input")

    spot_col = _find_column(df.columns, COLUMN_ALIASES["spot"])
    if spot_col is None:
        raise ValueError("Underlying spot column not found in input")

    rate_col = _find_column(df.columns, COLUMN_ALIASES["rate"])
    div_col = _find_column(df.columns, COLUMN_ALIASES["dividend"])

    exp_dates = df[exp_col].apply(_parse_date)
    ttm_days = (exp_dates - trade_date).dt.days.astype(float)
    mask = ttm_days >= args.min_ttm_days
    df = df[mask].copy()
    if df.empty:
        raise ValueError("No rows left after applying maturity filter")
    ttm_years = ttm_days[mask] / 365.0

    iv = df[iv_col].astype(float)
    iv = iv.where(iv <= 1.0, iv / 100.0)  # convert percent to decimal

    bid = df[bid_col].astype(float)
    ask = df[ask_col].astype(float)
    mid_mask = (bid > 0) & (ask > 0)
    df = df[mid_mask].copy()
    if df.empty:
        raise ValueError("All rows filtered out due to non-positive bid/ask")

    ttm_years = ttm_years.loc[df.index]
    iv = iv.loc[df.index]
    bid = bid.loc[df.index]
    ask = ask.loc[df.index]

    # Use per-row spot when available; fallback to median to avoid NaNs.
    spot_series = pd.to_numeric(df[spot_col], errors="coerce")
    spot_value = float(spot_series.dropna().median())
    spot_series = spot_series.fillna(spot_value)

    rate_series = (
        _parse_rate(pd.to_numeric(df[rate_col], errors="coerce"), default=0.0)
        if rate_col
        else pd.Series(0.0, index=df.index)
    )
    div_series = (
        _parse_rate(pd.to_numeric(df[div_col], errors="coerce"), default=0.0)
        if div_col
        else pd.Series(0.0, index=df.index)
    )

    normalized = pd.DataFrame(
        {
            "date": trade_date.isoformat(),
            "ttm_years": ttm_years.values,
            "strike": pd.to_numeric(df[strike_col], errors="coerce").values,
            "mid_iv": iv.values,
            "put_call": df[type_col].map(_normalized_put_call).values,
            "spot": spot_series.values,
            "r": rate_series.values,
            "q": div_series.values,
            "bid": bid.values,
            "ask": ask.values,
        }
    )
    normalized = normalized.replace([np.inf, -np.inf], np.nan).dropna()
    normalized = normalized.sort_values(["ttm_years", "strike"]).reset_index(drop=True)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.symbol.lower()}_{trade_date.strftime('%Y%m%d')}.csv"
    normalized.to_csv(out_path, index=False, float_format="%.8f")

    metadata = {
        "input": str(raw_path),
        "output": str(out_path),
        "rows": int(len(normalized)),
        "trade_date": trade_date.isoformat(),
        "min_ttm_days": args.min_ttm_days,
        "columns": STANDARD_COLUMNS,
    }
    manifest_path = out_path.with_suffix(".json")
    manifest_path.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Wrote {out_path} ({len(normalized)} rows)")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()

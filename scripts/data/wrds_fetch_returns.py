#!/usr/bin/env python3
"""
Fetch daily returns for a ticker from WRDS (CRSP) or fallback to yfinance.

Outputs CSV with columns: date, ret (decimal), close.

Usage:
  python scripts/data/wrds_fetch_returns.py --ticker SPY --start 2018-01-01 --end 2023-01-01 --out data/spy_returns.csv
"""
import argparse
import os
import sys


def fetch_wrds(ticker: str, start: str, end: str):
    try:
        import pandas as pd
        import wrds
    except Exception as e:
        raise RuntimeError(f"wrds not available: {e}")
    db = wrds.Connection()
    # Map ticker to permco from CRSP stocknames
    qmap = f"""
        select distinct permco
        from crsp.stocknames
        where ticker = '{ticker}'
    """
    names = db.raw_sql(qmap)
    if names.empty:
        raise RuntimeError(f"No CRSP permco for ticker {ticker}")
    permco = int(names["permco"].iloc[0])
    q = f"""
        select date, ret, prc as close
        from crsp.dsf
        where permco = {permco}
          and date between '{start}' and '{end}'
    """
    df = db.raw_sql(q)
    df = df.dropna(subset=["ret"])
    df = df.sort_values("date")
    return df


def fetch_yf(ticker: str, start: str, end: str):
    try:
        import pandas as pd
        import yfinance as yf
    except Exception as e:
        raise RuntimeError(f"yfinance not available: {e}")
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        raise RuntimeError("No data from yfinance")
    data["ret"] = data["Adj Close"].pct_change()
    out = data[["ret", "Adj Close"]].dropna().rename(columns={"Adj Close": "close"})
    out = out.reset_index().rename(columns={"Date": "date"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        df = fetch_wrds(args.ticker, args.start, args.end)
    except Exception:
        df = fetch_yf(args.ticker, args.start, args.end)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df.to_csv(args.out, index=False)
    print("wrote", args.out)


if __name__ == "__main__":
    main()

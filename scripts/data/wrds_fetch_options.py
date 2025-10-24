#!/usr/bin/env python3
"""
Fetch OptionMetrics options data from WRDS and write a normalized CSV for calibration.

Environment:
  WRDS_USERNAME, WRDS_PASSWORD (optional if .pgpass configured)

Usage:
  python scripts/data/wrds_fetch_options.py --date 2023-06-01 --underlying SPX --out data/options_2023-06-01.csv

The output CSV has columns:
  call_put, strike, mid, rate, q, spot, maturity_years
"""
import argparse
import datetime as dt
import os
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='Trade date YYYY-MM-DD')
    ap.add_argument('--underlying', default='SPX', help='Underlying symbol (e.g., SPX)')
    ap.add_argument('--out', required=True, help='Output CSV path')
    args = ap.parse_args()

    try:
        import wrds
        import pandas as pd
    except Exception as e:
        print('error: requires wrds and pandas packages: {}'.format(e), file=sys.stderr)
        sys.exit(1)

    date = pd.to_datetime(args.date).date()
    db = wrds.Connection()

    # Fetch underlying spot and rates/dividends proxies (simplified placeholders)
    # Users can post-process the CSV to refine r and q per maturity.
    # OptionMetrics schema can vary; adjust as needed.
    query = f"""
        select o.exdate, o.strike_price/1000.0 as strike,
               o.best_bid, o.best_offer, o.cp_flag,
               o.under_cusip, o.date, o.impl_volatility, o.volume,
               s.under_price
        from optionm.opprcd as o
        join optionm.secprd as s on o.secid = s.secid and o.date = s.date
        where o.symbol = '{args.underlying}' and o.date = '{date}'
    """
    try:
        df = db.raw_sql(query)
    except Exception as e:
        print('WRDS query failed: {}'.format(e), file=sys.stderr)
        sys.exit(2)

    if df.empty:
        print('No rows returned for date {}'.format(date), file=sys.stderr)
        sys.exit(3)

    df['mid'] = (df['best_bid'].fillna(0) + df['best_offer'].fillna(0)) / 2.0
    df['spot'] = df['under_price']
    df['maturity_years'] = (pd.to_datetime(df['exdate']).dt.date - pd.to_datetime(df['date']).dt.date).dt.days / 365.0
    df = df[(df['maturity_years'] > 1/365.0) & (df['mid'] > 0)]
    df['call_put'] = df['cp_flag'].map({'C': 'call', 'P': 'put'})

    # Simplified flat r and q (user may post-edit). Set q=0 for index, r from FRED or 2% placeholder.
    df['rate'] = 0.02
    df['q'] = 0.00

    out = df[['call_put', 'strike', 'mid', 'rate', 'q', 'spot', 'maturity_years']].copy()
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    out.to_csv(args.out, index=False)
    print('wrote', args.out)

if __name__ == '__main__':
    main()



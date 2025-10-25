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

    # OptionMetrics is year-partitioned at many institutions.
    # Prefer opprcdYYYY/secprdYYYY, fallback to non-partitioned or standardized views.
    year = str(date.year)
    candidates = [
        (f"optionm.opprcd{year}", f"optionm.secprd{year}"),
        (f"optionm.option_price_{year}", "optionm.security_price"),
    ]

    df = None
    last_err = None
    for op_tbl, sec_tbl in candidates:
        try:
            query = f"""
                select o.exdate,
                       o.strike_price/1000.0 as strike,
                       o.best_bid, o.best_offer, o.cp_flag,
                       o.date,
                       sp.under_price
                from {op_tbl} as o
                join optionm.security as sec on o.secid = sec.secid
                join {sec_tbl} as sp on o.secid = sp.secid and o.date = sp.date
                where o.date = '{date}'
                  and (sec.symbol = '{args.underlying}' or sec.symbol ilike '{args.underlying}%')
            """
            df_try = db.raw_sql(query)
            if df_try is not None and not df_try.empty:
                df = df_try
                break
        except Exception as e:
            last_err = e
            df = None
            continue

    if df is None or df.empty:
        print('WRDS query failed or returned no rows: {}'.format(last_err), file=sys.stderr)
        sys.exit(2)

    if df.empty:
        print('No rows returned for date {}'.format(date), file=sys.stderr)
        sys.exit(3)

    df['mid'] = (df['best_bid'].fillna(0) + df['best_offer'].fillna(0)) / 2.0
    # Some sites store as UNDER_PRICE or other case variations
    under_candidates = [c for c in df.columns if c.lower() == 'under_price']
    if under_candidates:
        df['spot'] = df[under_candidates[0]]
    else:
        # Fallback: use forward price if present, otherwise abort
        if 'under_price' in df.columns:
            df['spot'] = df['under_price']
        else:
            print('Could not locate under_price column in security price table', file=sys.stderr)
            sys.exit(4)
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



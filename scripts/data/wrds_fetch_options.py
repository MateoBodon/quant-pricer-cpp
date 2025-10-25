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
    ap.add_argument('--min_moneyness', type=float, default=0.6, help='Minimum K/S to retain')
    ap.add_argument('--max_moneyness', type=float, default=1.4, help='Maximum K/S to retain')
    ap.add_argument('--min_days', type=int, default=2, help='Minimum calendar days to expiry')
    args = ap.parse_args()

    try:
        import wrds
        import pandas as pd
        import psycopg2
    except Exception as e:
        print('error: requires wrds and pandas packages: {}'.format(e), file=sys.stderr)
        sys.exit(1)

    date = pd.to_datetime(args.date).date()
    db = wrds.Connection()

    # OptionMetrics is year-partitioned; use the tables visible in your site:
    # - optionm.opprcdYYYY (option quotes with symbol, cp_flag, strike_price, bids/offers)
    # - optionm.secprdYYYY (security prices with close)
    year = str(date.year)
    op_tbl = f"optionm.opprcd{year}"
    sec_tbl = f"optionm.secprd{year}"

    # Strategy: (1) pull options slice; (2) pull underlying closes for those secids; (3) merge in pandas
    last_err = None
    try:
        def sql_df(engine, q):
            # Bypass pandas+sqlalchemy param issues using raw cursor
            conn = engine.raw_connection()
            try:
                cur = conn.cursor()
                try:
                    cur.execute(q)
                    cols = [c[0] for c in cur.description]
                    rows = cur.fetchall()
                    import pandas as _pd
                    return _pd.DataFrame(rows, columns=cols)
                finally:
                    cur.close()
            finally:
                conn.close()

        opt_query = f"""
            select secid, symbol, exdate, cp_flag, strike_price, best_bid, best_offer, date
            from {op_tbl}
            where date = '{date}'
              and (symbol = '{args.underlying}' or symbol ilike '{args.underlying}%')
        """
        opt = sql_df(db.engine, opt_query)
        if opt is None or opt.empty:
            print('No option quotes for given date/symbol', file=sys.stderr)
            sys.exit(2)

        # Pull secprd for these secids in chunks
        import math
        secids = sorted({int(x) for x in opt['secid'].dropna().astype(int).tolist()})
        closes = []
        chunk_size = 200
        for i in range(0, len(secids), chunk_size):
            chunk = ",".join(str(s) for s in secids[i:i+chunk_size])
            sp_query = f"""
                select secid, date, close
                from {sec_tbl}
                where date = '{date}' and secid in ({chunk})
            """
            part = sql_df(db.engine, sp_query)
            if part is not None and not part.empty:
                closes.append(part)
        import pandas as pd
        if not closes:
            print('No underlying close prices for selected secids/date', file=sys.stderr)
            sys.exit(2)
        sp = pd.concat(closes, ignore_index=True)
        df = opt.merge(sp, on=['secid', 'date'], how='inner')
        if df.empty:
            print('Join produced no rows (secid/date mismatch)', file=sys.stderr)
            sys.exit(2)
        # Align column expected downstream
        df = df.rename(columns={'close': 'under_price', 'strike_price': 'strike'})
        # Ensure dates are datetime
        df['exdate'] = pd.to_datetime(df['exdate'])
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        last_err = e
        df = None

    if df is None or df.empty:
        print('WRDS query failed or returned no rows: {}'.format(last_err), file=sys.stderr)
        sys.exit(2)

    if df.empty:
        print('No rows returned for date {}'.format(date), file=sys.stderr)
        sys.exit(3)

    # Robust mid: if one side missing, use the other; drop if both missing
    import numpy as np
    bb = df['best_bid'].astype(float)
    bo = df['best_offer'].astype(float)
    # Fix crossed markets by swapping where needed
    mask_cross = (bb.notna()) & (bo.notna()) & (bb > bo)
    if mask_cross.any():
        tmp = bb[mask_cross].copy()
        bb.loc[mask_cross] = bo[mask_cross]
        bo.loc[mask_cross] = tmp
    mid = np.where(bb.notna() & bo.notna(), 0.5 * (bb.to_numpy() + bo.to_numpy()),
                   np.where(bb.notna(), bb.to_numpy(), np.where(bo.notna(), bo.to_numpy(), np.nan)))
    df['mid'] = mid
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
    days = (df['exdate'] - df['date']).dt.days
    df['maturity_years'] = days / 365.0
    df = df[(days >= args.min_days)]
    df = df[np.isfinite(df['mid']) & (df['mid'] > 0)]
    df['call_put'] = df['cp_flag'].map({'C': 'call', 'P': 'put'})

    # Simplified flat r and q (user may post-edit). Set q=0 for index, r from FRED or 2% placeholder.
    df['rate'] = 0.02
    df['q'] = 0.00

    # Moneyness filter
    df['moneyness'] = df['strike'] / df['spot']
    df = df[(df['moneyness'] >= args.min_moneyness) & (df['moneyness'] <= args.max_moneyness)]

    out = df[['call_put', 'strike', 'mid', 'rate', 'q', 'spot', 'maturity_years']].copy()
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    out.to_csv(args.out, index=False)
    print('wrote', args.out)

if __name__ == '__main__':
    main()



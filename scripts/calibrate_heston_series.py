#!/usr/bin/env python3
"""
Batch Heston calibration over a date range: fetch options via WRDS, calibrate, and store parameter time series.

Usage:
  python scripts/calibrate_heston_series.py --underlying SPX --start 2023-05-01 --end 2023-05-31 --out artifacts/heston_series.csv
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

import pandas as pd


def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--underlying', default='SPX')
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    start = dt.datetime.strptime(args.start, '%Y-%m-%d').date()
    end = dt.datetime.strptime(args.end, '%Y-%m-%d').date()
    day = start
    rows = []
    os.makedirs('data', exist_ok=True)
    os.makedirs('artifacts', exist_ok=True)
    while day <= end:
        options_csv = f'data/options_{day}.csv'
        calib_json = f'artifacts/heston_calib_{day}.json'
        try:
            run([sys.executable, 'scripts/data/wrds_fetch_options.py', '--date', str(day), '--underlying', args.underlying, '--out', options_csv])
            run([sys.executable, 'scripts/calibrate_heston.py', '--csv', options_csv, '--out', calib_json])
            with open(calib_json, 'r') as fh:
                params = json.load(fh)
            rows.append({'date': str(day), **params})
            print('calibrated', day)
        except Exception as e:
            print('warn:', e, 'for date', day)
        day += dt.timedelta(days=1)

    if not rows:
        print('no calibrations produced', file=sys.stderr)
        sys.exit(1)
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print('wrote', args.out)


if __name__ == '__main__':
    main()



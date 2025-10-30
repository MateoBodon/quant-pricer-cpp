# Data Directory

## Normalized Surface Schema

All option-surface CSVs consumed by the calibration scripts follow the schema
described below (see also `scripts/data/schema.md`). Values are in base units
unless stated otherwise.

| Column      | Type  | Units / Notes                                                  |
|-------------|-------|----------------------------------------------------------------|
| `date`      | str   | Trade date in ISO `YYYY-MM-DD` format.                        |
| `ttm_years` | float | Time-to-maturity in years (calendar days ÷ 365).              |
| `strike`    | float | Option strike price.                                          |
| `mid_iv`    | float | Mid implied volatility (Black–Scholes, decimal: e.g. `0.23`). |
| `put_call`  | str   | `call` or `put`.                                              |
| `spot`      | float | Underlying spot level on `date`.                              |
| `r`         | float | Continuously compounded risk-free rate.                       |
| `q`         | float | Continuously compounded dividend or funding yield.            |
| `bid`       | float | Best bid option price (same currency as strike).              |
| `ask`       | float | Best ask option price.                                        |

## Provenance & Licensing

- `data/samples/spx_20240614_sample.csv` is a tiny **synthetic** SPX surface
  generated from the Black–Scholes model for CI and documentation examples. It
  contains two expiries × twelve strikes (≤ 20 rows) to keep PR runs fast.
- No third-party market data is distributed in this repository. For production
  calibration, source CBOE/WRDS data under their respective licenses.

## Swapping Datasets

All driver scripts accept an `--input` flag. For example, to calibrate Heston
on a new normalized CSV:

```bash
python scripts/calibrate_heston.py --input data/normalized/spx_20250117.csv --fast
```

Use `scripts/data/cboe_csv.py` (or your own adapter) to convert raw exports
into the schema above before invoking the calibration scripts.

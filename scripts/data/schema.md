# Option Surface Schema

The normalization helpers emit CSV files with the following columns. All scripts
in `scripts/calibrate_*.py` assume this exact schema.

| Column      | Type   | Description                                                                          |
|-------------|--------|--------------------------------------------------------------------------------------|
| `date`      | string | Trade date in ISO format `YYYY-MM-DD`.                                               |
| `ttm_years` | float  | Time-to-maturity in **years** (calendar days divided by 365).                        |
| `strike`    | float  | Option strike.                                                                       |
| `mid_iv`    | float  | Mid implied volatility (Black-Scholes, decimal units, e.g. `0.213`).                 |
| `put_call`  | string | Option type: `"put"` or `"call"`.                                                    |
| `spot`      | float  | Underlying spot level for the trade date.                                            |
| `r`         | float  | Continuously compounded risk-free short rate for the maturity.                       |
| `q`         | float  | Continuously compounded dividend yield (or funding) for the maturity.                |
| `bid`       | float  | Best bid option price (same currency as spot).                                       |
| `ask`       | float  | Best ask option price.                                                               |

Additional columns are ignored by downstream scripts, but these ten columns
must be present to ensure deterministic Heston calibration and validation runs.

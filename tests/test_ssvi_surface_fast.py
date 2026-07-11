#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wrds_pipeline.bs_utils import bs_call, bs_vega  # noqa: E402
from wrds_pipeline.ssvi_reference import (  # noqa: E402
    quantlib_ssvi_arbitrage_audit,
)
from wrds_pipeline.ssvi_surface import (  # noqa: E402
    KNOT_BUCKETS,
    KNOT_YEARS,
    SsviCalibrationConfig,
    SsviParameters,
    apply_surface,
    arbitrage_diagnostics,
    atm_total_variance,
    calibrate,
    model_iv,
    summarize_oos,
)
from ssvi_development_benchmark import _frequency_weighted_stats  # noqa: E402
from ssvi_five_date_panel import PANEL_ENTRIES  # noqa: E402


def _synthetic_surface(params: SsviParameters) -> pd.DataFrame:
    rows = []
    for bucket, maturity in zip(KNOT_BUCKETS, KNOT_YEARS):
        for log_moneyness in np.linspace(-0.30, 0.30, 21):
            spot = 100.0
            rate = 0.02
            dividend = 0.01
            forward = spot * np.exp((rate - dividend) * maturity)
            strike = forward * np.exp(log_moneyness)
            volatility = model_iv(
                spot=spot,
                strike=float(strike),
                rate=rate,
                dividend=dividend,
                maturity=float(maturity),
                params=params,
            )
            rows.append(
                {
                    "symbol": "SPX",
                    "trade_date": "2024-01-02",
                    "quote_date": "2024-01-02",
                    "tenor_bucket": bucket,
                    "moneyness": float(strike / spot),
                    "ttm_years": float(maturity),
                    "days_to_expiration": round(float(maturity) * 365.0),
                    "spot": spot,
                    "strike": float(strike),
                    "rate": rate,
                    "dividend": dividend,
                    "mid_price": bs_call(
                        spot,
                        float(strike),
                        rate,
                        dividend,
                        volatility,
                        float(maturity),
                    ),
                    "mid_iv": volatility,
                    "vega": bs_vega(
                        spot,
                        float(strike),
                        rate,
                        dividend,
                        volatility,
                        float(maturity),
                    ),
                    "quotes": 10,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    if len(PANEL_ENTRIES) != 5:
        raise AssertionError("The fixed SSVI development panel must contain five dates")
    frequency_stats = _frequency_weighted_stats(
        pd.Series([1.0, 3.0]),
        pd.Series([1, 3]),
    )
    if frequency_stats != {"mean": 2.5, "sigma": 1.0, "quote_weight": 4}:
        raise AssertionError("Frequency-weighted hedge reducer changed")
    nonpositive_frequency_stats = _frequency_weighted_stats(
        pd.Series([1.0, 100.0]),
        pd.Series([2, 0]),
    )
    if nonpositive_frequency_stats != {
        "mean": 1.0,
        "sigma": 0.0,
        "quote_weight": 2,
    }:
        raise AssertionError("Nonpositive quote frequencies must be excluded")

    true_params = SsviParameters(
        theta_knots=(0.006, 0.011, 0.016, 0.030, 0.055),
        rho=-0.70,
        eta=0.50,
        gamma=0.50,
    )
    config = SsviCalibrationConfig(max_evals=300)
    theta_grid = np.asarray(
        atm_total_variance(np.linspace(0.01, 1.25, 100), true_params.theta_knots)
    )
    if np.any(np.diff(theta_grid) <= 0.0):
        raise AssertionError("SSVI ATM total variance curve is not strictly increasing")

    surface = _synthetic_surface(true_params)
    result = calibrate(surface, config)
    diagnostics = result["diagnostics"]
    if diagnostics["promotion_status"] != "eligible":
        raise AssertionError(f"Synthetic SSVI fit was gated: {diagnostics}")
    if result["metrics"]["iv_rmse_volpts_vega_wt"] > 1e-8:
        raise AssertionError("SSVI synthetic recovery IV RMSE exceeds tolerance")
    if result["metrics"]["price_rmse_ticks"] > 1e-5:
        raise AssertionError("SSVI synthetic recovery price RMSE exceeds tolerance")
    if diagnostics["multistart_count"] != 3:
        raise AssertionError("Expected three deterministic SSVI starts")
    if diagnostics["price_output_clipped"] is not False:
        raise AssertionError("SSVI price clipping was enabled")

    independent = quantlib_ssvi_arbitrage_audit(result["params"], config)
    if independent["status"] != "valid":
        raise AssertionError(f"Independent QuantLib SSVI audit failed: {independent}")
    if independent["max_price_abs_error_vs_quantlib"] > 1e-10:
        raise AssertionError("Repository and QuantLib Black prices disagree")
    if independent["evaluated_price_count"] != 1089:
        raise AssertionError("Independent SSVI grid cardinality changed")

    reapplied = apply_surface(surface, result["params"])
    oos = summarize_oos(reapplied)
    if oos["invalid_rows"] != 0 or oos["iv_mae_bps"] > 1e-4:
        raise AssertionError("SSVI reapplication produced invalid or inaccurate rows")

    invalid_params = SsviParameters(
        theta_knots=true_params.theta_knots,
        rho=0.99,
        eta=20.0,
        gamma=0.50,
    )
    invalid = arbitrage_diagnostics(invalid_params, config)
    if invalid["status"] != "invalid":
        raise AssertionError("Arbitrage-violating SSVI parameters passed the gate")
    if invalid["analytic_sufficient_conditions_pass"] is not False:
        raise AssertionError("Expected sufficient SSVI conditions to fail")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Minimal runtime smoke test executed inside cibuildwheel.

Ensures the pyquant_pricer wheel imports, exercises BS pricing,
and touches the Heston helpers (analytic IV + characteristic fn).
"""
from __future__ import annotations

import math

import numpy as np
import pyquant_pricer as qp


def main() -> None:
    call = qp.bs_call(100.0, 105.0, 0.02, 0.0, 0.25, 0.5)
    assert math.isclose(call, 5.376620585926435, rel_tol=0.0, abs_tol=1e-12)

    hparams = qp.HestonParams()
    hparams.kappa = 1.4
    hparams.theta = 0.04
    hparams.sigma = 0.5
    hparams.rho = -0.6
    hparams.v0 = 0.04

    market = qp.HestonMarket()
    market.spot = 100.0
    market.strike = 95.0
    market.rate = 0.01
    market.dividend = 0.0
    market.time = 0.75

    iv = qp.heston_implied_vol(market, hparams)
    assert 0.05 < iv < 1.0
    cf = qp.heston_characteristic_fn(0.5, market, hparams)
    assert isinstance(cf, complex)
    assert abs(cf) > 0.0
    scalar_price = qp.heston_call_analytic(market, hparams)
    markets = np.array([[100.0, 95.0, 0.01, 0.0, 0.75]])
    params = np.array([[1.4, 0.04, 0.5, -0.6, 0.04]])
    assert qp.heston_calls_analytic_batch(markets, params).tolist() == [scalar_price]
    assert qp.heston_implied_vols_batch(markets, params).tolist() == [iv]
    assert qp.heston_call_metrics_batch(markets, params).tolist() == [
        [scalar_price, iv]
    ]
    assert len(qp.heston_call_metrics_batch(markets, np.repeat(params, 2, axis=0))) == 2
    assert qp.heston_call_metrics_grid(markets, params).tolist() == [
        [[scalar_price, iv]]
    ]
    assert qp.heston_analytic_batch_policy() == {
        "max_process_workers": 4,
        "items_per_worker": 32,
    }
    assert (
        len(qp.heston_calls_analytic_batch(np.repeat(markets, 2, axis=0), params)) == 2
    )
    try:
        qp.heston_calls_analytic_batch(
            np.repeat(markets, 3, axis=0), np.repeat(params, 2, axis=0)
        )
    except ValueError as exc:
        assert "one row or match" in str(exc)
    else:
        raise AssertionError("mismatched Heston batch inputs must fail closed")


if __name__ == "__main__":
    main()

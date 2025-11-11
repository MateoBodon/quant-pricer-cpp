#!/usr/bin/env python3
"""
Minimal runtime smoke test executed inside cibuildwheel.

Ensures the pyquant_pricer wheel imports, exercises BS pricing,
and touches the Heston helpers (analytic IV + characteristic fn).
"""
from __future__ import annotations

import math

import pyquant_pricer as qp


def main() -> None:
    call = qp.bs_call(100.0, 105.0, 0.02, 0.0, 0.25, 0.5)
    assert math.isclose(call, 4.550194, rel_tol=0.0, abs_tol=1e-6)

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


if __name__ == "__main__":
    main()

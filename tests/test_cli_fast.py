#!/usr/bin/env python3
"""FAST-tier smoke tests for the quant_cli front-end.

Exercises every engine (bs, iv, mc, barrier, american, pde, digital, asian,
lookback, heston, risk) to ensure argument parsing stays wired up and to boost
coverage for src/main.cpp without re-implementing the CLI in C++ tests.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, List


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_common(
    spot: float,
    strike: float,
    rate: float,
    dividend: float,
    sigma: float,
    time: float,
) -> tuple[float, float, float, float]:
    if time <= 0.0 or sigma <= 0.0:
        df_r = math.exp(-rate * max(time, 0.0))
        df_q = math.exp(-dividend * max(time, 0.0))
        forward_call = max(0.0, spot * df_q - strike * df_r)
        forward_put = max(0.0, strike * df_r - spot * df_q)
        return forward_call, forward_put, 0.0, 0.0
    sqrt_t = math.sqrt(time)
    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * sigma * sigma) * time) / (
        sigma * sqrt_t
    )
    d2 = d1 - sigma * sqrt_t
    df_r = math.exp(-rate * time)
    df_q = math.exp(-dividend * time)
    call = spot * df_q * _norm_cdf(d1) - strike * df_r * _norm_cdf(d2)
    put = strike * df_r * _norm_cdf(-d2) - spot * df_q * _norm_cdf(-d1)
    return call, put, d1, d2


def bs_call_price(
    spot: float, strike: float, rate: float, dividend: float, sigma: float, time: float
) -> float:
    call, _, _, _ = _bs_common(spot, strike, rate, dividend, sigma, time)
    return call


def bs_put_price(
    spot: float, strike: float, rate: float, dividend: float, sigma: float, time: float
) -> float:
    _, put, _, _ = _bs_common(spot, strike, rate, dividend, sigma, time)
    return put


def cash_or_nothing_call(
    spot: float, strike: float, rate: float, dividend: float, sigma: float, time: float
) -> float:
    _, _, _, d2 = _bs_common(spot, strike, rate, dividend, sigma, time)
    if time <= 0.0 or sigma <= 0.0:
        payoff = 1.0 if spot > strike else 0.0
        return payoff * math.exp(-rate * max(time, 0.0))
    return math.exp(-rate * time) * _norm_cdf(d2)


def run_cli_plain(cli: Path, *args: str) -> str:
    cmd = [str(cli), *args]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    out = proc.stdout.strip()
    if not out:
        raise AssertionError(f"{' '.join(cmd)} returned empty stdout")
    return out


def run_cli_json(cli: Path, *args: str) -> Any:
    final_args = list(args)
    if "--json" not in final_args:
        final_args.append("--json")
    out = run_cli_plain(cli, *final_args)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        sanitized = re.sub(r"\binf\b", "Infinity", out)
        return json.loads(sanitized)


def assert_close(actual: float, expected: float, tol: float, msg: str) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(f"{msg}: {actual} vs {expected} (tol={tol})")


def assert_between(value: float, low: float, high: float, msg: str) -> None:
    if not (low <= value <= high):
        raise AssertionError(f"{msg}: {value} not in [{low}, {high}]")


def smoke_cli(cli: Path) -> None:
    # Black–Scholes analytics + implied vol
    spot, strike, rate, div, vol, tenor = 100.0, 95.0, 0.01, 0.005, 0.22, 0.75
    bs_json = run_cli_json(
        cli,
        "bs",
        f"{spot}",
        f"{strike}",
        f"{rate}",
        f"{div}",
        f"{vol}",
        f"{tenor}",
        "call",
    )
    reference_call = bs_call_price(spot, strike, rate, div, vol, tenor)
    assert_close(bs_json["price"], reference_call, 5e-4, "BS call mismatch")

    iv_json = run_cli_json(
        cli,
        "iv",
        "call",
        f"{spot}",
        f"{strike}",
        f"{rate}",
        f"{div}",
        f"{tenor}",
        f"{reference_call:.12f}",
    )
    assert_close(iv_json["iv"], vol, 1e-6, "Implied vol mismatch")

    # Monte Carlo (European)
    mc_json = run_cli_json(
        cli,
        "mc",
        "100",
        "100",
        "0.02",
        "0.01",
        "0.25",
        "0.5",
        "4096",
        "1337",
        "1",
        "sobol",
        "bb",
        "12",
        "--threads=1",
        "--sampler=none",
        "--bridge=none",
        "--steps=10",
        "--rng=counter",
        "--greeks",
        "--ci",
    )
    mc_ref = bs_call_price(100.0, 100.0, 0.02, 0.01, 0.25, 0.5)
    assert_between(mc_json["price"], mc_ref - 0.35, mc_ref + 0.35, "MC price drifted")
    assert_between(mc_json["std_error"], 0.0, 1.0, "MC std error invalid")
    assert mc_json["ci_low"] < mc_json["price"] < mc_json["ci_high"]
    assert mc_json["sampler"] == "prng"
    assert mc_json["bridge"] == "none"
    greeks = mc_json["greeks"]
    for key in ("delta", "vega", "gamma_lrm", "gamma_pathwise", "theta"):
        stat = greeks[key]
        assert "value" in stat
        assert "std_error" in stat

    # Barrier pricing (analytic vs MC vs PDE)
    barrier_bs = float(
        run_cli_plain(
            cli,
            "barrier",
            "bs",
            "call",
            "down",
            "out",
            "100",
            "95",
            "90",
            "0",
            "0.01",
            "0.0",
            "0.22",
            "0.5",
        )
    )
    barrier_mc = run_cli_json(
        cli,
        "barrier",
        "mc",
        "call",
        "down",
        "out",
        "100",
        "95",
        "90",
        "0",
        "0.01",
        "0.0",
        "0.22",
        "0.5",
        "2048",
        "4242",
        "1",
        "sobol",
        "bb",
        "16",
        "--rng=mt19937",
        "--ci",
    )
    assert_between(
        barrier_mc["price"], barrier_bs - 1.5, barrier_bs + 1.5, "Barrier MC off"
    )
    barrier_pde = run_cli_json(
        cli,
        "barrier",
        "pde",
        "call",
        "down",
        "out",
        "100",
        "95",
        "90",
        "0",
        "0.01",
        "0.0",
        "0.22",
        "0.5",
        "60",
        "80",
        "3.5",
    )
    assert_between(
        barrier_pde["price"], barrier_bs - 0.6, barrier_bs + 0.6, "Barrier PDE mismatch"
    )
    assert abs(barrier_pde["delta"]) <= 1.0

    # American variants
    amer_binom = run_cli_json(
        cli,
        "american",
        "binomial",
        "call",
        "100",
        "95",
        "0.01",
        "0.0",
        "0.25",
        "1.0",
        "64",
    )
    euro_call = bs_call_price(100.0, 95.0, 0.01, 0.0, 0.25, 1.0)
    assert_close(
        amer_binom["price"],
        euro_call,
        1e-2,
        "American binomial deviates for non-dividend call",
    )

    amer_psor = run_cli_json(
        cli,
        "american",
        "psor",
        "put",
        "90",
        "95",
        "0.015",
        "0.0",
        "0.3",
        "0.75",
        "80",
        "120",
        "4.5",
        "1",
        "0",
        "2.0",
        "1.4",
        "6000",
        "1e-8",
    )
    assert amer_psor["iterations"] > 0
    amer_lsmc = run_cli_json(
        cli,
        "american",
        "lsmc",
        "put",
        "90",
        "95",
        "0.015",
        "0.0",
        "0.3",
        "0.75",
        "2000",
        "32",
        "2025",
        "0",
    )
    assert len(amer_lsmc["itm_counts"]) >= 10
    assert amer_lsmc["std_error"] > 0.0

    # Vanilla PDE
    pde_json = run_cli_json(
        cli,
        "pde",
        "105",
        "100",
        "0.02",
        "0.01",
        "0.3",
        "0.5",
        "call",
        "80",
        "120",
        "4.0",
        "1",
        "1",
        "2.0",
        "1",
        "1",
    )
    assert abs(pde_json["delta"]) <= 1.0
    assert pde_json["theta"] is not None

    # Digitals
    digital_json = run_cli_json(
        cli,
        "digital",
        "cash",
        "call",
        "100",
        "110",
        "0.01",
        "0.0",
        "0.2",
        "0.5",
    )
    expected_digital = cash_or_nothing_call(100.0, 110.0, 0.01, 0.0, 0.2, 0.5)
    assert_close(
        digital_json["price"], expected_digital, 5e-4, "Digital price mismatch"
    )

    # Asian + lookback
    asian_json = run_cli_json(
        cli,
        "asian",
        "arith",
        "fixed",
        "100",
        "95",
        "0.01",
        "0.0",
        "0.25",
        "0.75",
        "2048",
        "24",
        "1337",
        "--no_cv",
    )
    assert asian_json["ci_low"] < asian_json["ci_high"]
    lookback_json = run_cli_json(
        cli,
        "lookback",
        "fixed",
        "call",
        "100",
        "95",
        "0.01",
        "0.0",
        "0.25",
        "0.5",
        "2048",
        "24",
        "101",
        "--no_anti",
    )
    assert lookback_json["price"] > 0.0

    # Heston analytic + MC
    heston_args: List[str] = [
        "heston",
        "1.5",
        "0.04",
        "0.5",
        "-0.4",
        "0.04",
        "100",
        "95",
        "0.01",
        "0.0",
        "0.75",
        "20000",
        "32",
        "99",
    ]
    heston_analytic = float(run_cli_plain(cli, *heston_args))
    heston_mc = run_cli_json(
        cli,
        *heston_args,
        "--mc",
        "--ci",
        "--no-anti",
        "--heston-euler",
        "--heston-qe",
        "--rng=counter",
    )
    assert_close(
        heston_mc["analytic"], heston_analytic, 1e-6, "Heston analytic not echoed"
    )
    assert_between(
        heston_mc["price"],
        heston_mc["ci_low"],
        heston_mc["ci_high"],
        "Heston MC CI invalid",
    )
    assert heston_mc["std_error"] > 0.0
    assert heston_mc["abs_error"] >= 0.0

    # Risk metrics
    risk_json = run_cli_json(
        cli,
        "risk",
        "gbm",
        "100",
        "0.02",
        "0.3",
        "1.0",
        "5.0",
        "5000",
        "42",
        "0.99",
    )
    assert risk_json["var"] > 0.0
    assert risk_json["cvar"] > risk_json["var"]


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quant-cli", required=True, help="Path to the quant_cli binary"
    )
    args = parser.parse_args(argv)
    cli_path = Path(args.quant_cli)
    if not cli_path.exists():
        raise SystemExit(f"quant_cli not found: {cli_path}")
    if not shutil.which(str(cli_path)):
        # On Windows CTest passes absolute path, so shutil.which returning None is ok.
        pass
    smoke_cli(cli_path)


if __name__ == "__main__":
    main()

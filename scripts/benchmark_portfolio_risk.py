#!/usr/bin/env python3
"""Deterministic before/after benchmark for the native portfolio-risk surface."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=7)
    return parser.parse_args()


def command_output(argv: list[str]) -> str:
    try:
        return subprocess.run(argv, check=True, capture_output=True, text=True).stdout.strip().splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return "unavailable"


def timed(repetitions: int, fn) -> tuple[float, list[float]]:
    fn()
    samples: list[float] = []
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - started) / 1e9)
    return statistics.median(samples), samples


def make_positions(count: int) -> np.ndarray:
    index = np.arange(count, dtype=np.float64)
    positions = np.empty((count, 8), dtype=np.float64)
    positions[:, 0] = np.where((index.astype(np.int64) & 1) == 0, 1.0, -1.0)
    positions[:, 1] = np.where((index.astype(np.int64) % 3) == 0, -2.0, 1.5)
    positions[:, 2] = 80.0 + np.mod(index * 0.37, 50.0)
    positions[:, 3] = 75.0 + np.mod(index * 0.53, 60.0)
    positions[:, 4] = -0.002 + np.mod(index.astype(np.int64), 7) * 0.01
    positions[:, 5] = np.mod(index.astype(np.int64), 5) * 0.005
    positions[:, 6] = 0.10 + np.mod(index.astype(np.int64), 9) * 0.045
    positions[:, 7] = (7.0 + np.mod(index.astype(np.int64), 720)) / 365.0
    return positions


def scalar_risk_baseline(qp, positions: np.ndarray) -> float:
    # Existing installed surface exposes call price, delta, gamma, and vega as
    # scalar calls. The native candidate computes these plus theta/rho and puts.
    total = 0.0
    for row in positions:
        _, quantity, spot, strike, rate, dividend, volatility, time_to_expiry = row
        total += quantity * qp.bs_call(spot, strike, rate, dividend, volatility, time_to_expiry)
        total += quantity * qp.bs_delta_call(spot, strike, rate, dividend, volatility, time_to_expiry)
        total += quantity * qp.bs_gamma(spot, strike, rate, dividend, volatility, time_to_expiry)
        total += quantity * qp.bs_vega(spot, strike, rate, dividend, volatility, time_to_expiry)
    return total


def scalar_scenario_baseline(qp, positions: np.ndarray, shocks: np.ndarray) -> np.ndarray:
    base: list[float] = []
    for row in positions:
        option_type, quantity, spot, strike, rate, dividend, volatility, time_to_expiry = row
        pricer = qp.bs_call if option_type == 1.0 else qp.bs_put
        base.append(quantity * pricer(spot, strike, rate, dividend, volatility, time_to_expiry))
    output = np.empty(len(shocks), dtype=np.float64)
    for shock_index, shock in enumerate(shocks):
        spot_return, vol_shift, rate_shift, dividend_shift, time_elapsed = shock
        total = 0.0
        for position_index, row in enumerate(positions):
            option_type, quantity, spot, strike, rate, dividend, volatility, time_to_expiry = row
            pricer = qp.bs_call if option_type == 1.0 else qp.bs_put
            shocked_price = pricer(
                spot * (1.0 + spot_return), strike, rate + rate_shift, dividend + dividend_shift,
                volatility + vol_shift, max(0.0, time_to_expiry - time_elapsed),
            )
            total += quantity * shocked_price - base[position_index]
        output[shock_index] = total
    return output


def main() -> int:
    args = parse_args()
    if args.repetitions < 7:
        raise SystemExit("at least seven repetitions are required")
    sys.path.insert(0, str(args.module_dir.resolve()))
    import pyquant_pricer as qp
    import QuantLib as ql

    risk_positions = make_positions(100_000)
    # Scalar baseline is call-only because the incumbent exposes no scalar put
    # delta/theta/rho surface. Native still computes the full call risk vector.
    scalar_risk_positions = risk_positions[:100_000].copy()
    scalar_risk_positions[:, 0] = 1.0
    scenario_positions = make_positions(20_000)
    shocks = np.asarray(
        [
            [-0.30 + 0.04 * i, 0.14 - 0.015 * (i % 7), -0.02 + 0.004 * (i % 9),
             -0.006 + 0.002 * (i % 6), (i % 8) / 365.0]
            for i in range(16)
        ],
        dtype=np.float64,
    )

    risk_native_median, risk_native_samples = timed(
        args.repetitions, lambda: qp.bs_portfolio_risk(scalar_risk_positions)
    )
    risk_scalar_median, risk_scalar_samples = timed(
        args.repetitions, lambda: scalar_risk_baseline(qp, scalar_risk_positions)
    )
    scenario_native_median, scenario_native_samples = timed(
        args.repetitions, lambda: qp.bs_portfolio_scenarios(scenario_positions, shocks, False)
    )
    scenario_scalar_median, scenario_scalar_samples = timed(
        args.repetitions, lambda: scalar_scenario_baseline(qp, scenario_positions, shocks)
    )

    native_scenarios = qp.bs_portfolio_scenarios(scenario_positions, shocks, False)["portfolio_pnl"]
    scalar_scenarios = scalar_scenario_baseline(qp, scenario_positions, shocks)
    np.testing.assert_allclose(native_scenarios, scalar_scenarios, rtol=1e-12, atol=1e-9)
    deterministic = [qp.bs_portfolio_scenarios(scenario_positions, shocks, False)["portfolio_pnl"] for _ in range(5)]
    for repeated in deterministic:
        np.testing.assert_array_equal(repeated, native_scenarios)

    risk_speedup = risk_scalar_median / risk_native_median
    scenario_speedup = scenario_scalar_median / scenario_native_median
    if risk_speedup < 10.0 or scenario_speedup < 10.0:
        raise AssertionError(f"frozen performance gate failed: risk={risk_speedup:.3f}x scenario={scenario_speedup:.3f}x")

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() != "Darwin":
        peak_rss *= 1024
    repo_root = Path(__file__).resolve().parents[1]
    receipt = {
        "schema_version": 1,
        "benchmark_id": "bs_portfolio_risk_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "repetitions": args.repetitions,
            "statistic": "median_after_one_warmup",
            "risk_positions": len(scalar_risk_positions),
            "scenario_positions": len(scenario_positions),
            "scenario_count": len(shocks),
            "performance_gate_speedup": 10.0,
            "seed_or_randomness": "none; formula-generated deterministic matrices",
        },
        "results": {
            "risk_native_median_seconds": risk_native_median,
            "risk_scalar_median_seconds": risk_scalar_median,
            "risk_speedup": risk_speedup,
            "risk_native_positions_per_second": len(scalar_risk_positions) / risk_native_median,
            "scenario_native_median_seconds": scenario_native_median,
            "scenario_scalar_median_seconds": scenario_scalar_median,
            "scenario_speedup": scenario_speedup,
            "scenario_native_cells_per_second": len(scenario_positions) * len(shocks) / scenario_native_median,
            "risk_native_samples_seconds": risk_native_samples,
            "risk_scalar_samples_seconds": risk_scalar_samples,
            "scenario_native_samples_seconds": scenario_native_samples,
            "scenario_scalar_samples_seconds": scenario_scalar_samples,
            "deterministic_repetitions": 5,
            "scalar_parity_max_abs_pnl": float(np.max(np.abs(native_scenarios - scalar_scenarios))),
        },
        "resources": {
            "peak_process_rss_bytes": int(peak_rss),
            "risk_input_bytes": int(scalar_risk_positions.nbytes),
            "risk_output_bytes": int(len(scalar_risk_positions) * 7 * 8 + 6 * 8),
            "scenario_input_bytes": int(scenario_positions.nbytes + shocks.nbytes),
            "scenario_aggregate_output_bytes": int(len(shocks) * 8),
            "scenario_detail_output_bytes_if_requested": int(len(shocks) * len(scenario_positions) * 8),
        },
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu": command_output(["sysctl", "-n", "machdep.cpu.brand_string"]),
            "logical_cpus": os.cpu_count(),
            "memory_bytes": command_output(["sysctl", "-n", "hw.memsize"]),
            "compiler": command_output(["c++", "--version"]),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "quantlib": ql.__version__,
            "pyquant_pricer": qp.__version__,
            "git_head": command_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"]),
        },
        "claim_boundary": (
            "Hardware/protocol-specific Python orchestration comparison; deterministic Black-Scholes pricing and "
            "conditional stress only, not a market-risk, hedge, PnL, or trading claim."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"risk_speedup": risk_speedup, "scenario_speedup": scenario_speedup,
                      "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

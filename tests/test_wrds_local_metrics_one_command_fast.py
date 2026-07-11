#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wrds_pipeline.calibrate_heston import (  # noqa: E402
    LOWER_BOUNDS,
    REFERENCE_LAGUERRE_SCALE,
    REFERENCE_QUADRATURE_POINTS,
    calibration_diagnostics,
    heston_call_price,
)
from wrds_pipeline import delta_hedge_pnl  # noqa: E402
from wrds_pipeline.delta_hedge_pnl import heston_delta_call  # noqa: E402
from wrds_pipeline.heston_reference import (  # noqa: E402
    quantlib_heston_call_price,
    quantlib_heston_delta,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_calibration_gate_unit_cases() -> None:
    result = SimpleNamespace(
        success=True,
        status=1,
        nfev=12,
        njev=4,
        cost=0.25,
        optimality=1e-8,
        message="ok",
    )
    interior = np.array([1.0, 0.05, 0.5, -0.5, 0.04], dtype=float)
    eligible = calibration_diagnostics(result, interior)
    if eligible["promotion_status"] != "eligible":
        raise AssertionError("Interior converged fit should be eligible")

    saturated = interior.copy()
    saturated[0] = LOWER_BOUNDS[0]
    diagnostic = calibration_diagnostics(result, saturated)
    if diagnostic["promotion_status"] != "boundary_saturated":
        raise AssertionError("Bound-active fit must be diagnostic-only")
    if diagnostic["promotion_eligible"] is not False:
        raise AssertionError("Bound-active fit cannot be promotion eligible")
    if diagnostic["active_bound_params"] != ["kappa"]:
        raise AssertionError("Expected exact kappa lower-bound attribution")

    params = {
        "kappa": 1.5,
        "theta": 0.04,
        "sigma": 0.5,
        "rho": -0.5,
        "v0": 0.04,
    }
    delta = heston_delta_call(
        spot=100.0,
        strike=100.0,
        rate=0.01,
        div=0.0,
        T=1.0,
        params=params,
    )
    delta_half_bump = heston_delta_call(
        spot=100.0,
        strike=100.0,
        rate=0.01,
        div=0.0,
        T=1.0,
        params=params,
        relative_bump=5e-5,
    )
    if not 0.0 < delta < 1.0:
        raise AssertionError(f"Invalid Heston delta {delta}")
    if abs(delta - delta_half_bump) > 1e-4:
        raise AssertionError("Heston delta is unstable under a halved bump")

    diagnostic = delta_hedge_pnl.heston_delta_diagnostic(
        spot=100.0,
        strike=100.0,
        rate=0.01,
        div=0.0,
        T=1.0,
        params=params,
    )
    if not diagnostic.valid or diagnostic.invalid_reasons:
        raise AssertionError("Stable interior Heston delta should be valid")

    original_pricer = delta_hedge_pnl.heston_call_price

    def _invalid_slope_pricer(**kwargs: object) -> float:
        return 2.0 * float(kwargs["spot"])

    delta_hedge_pnl.heston_call_price = _invalid_slope_pricer
    try:
        invalid = delta_hedge_pnl.heston_delta_diagnostic(
            spot=100.0,
            strike=100.0,
            rate=0.01,
            div=0.0,
            T=1.0,
            params=params,
        )
        if invalid.valid:
            raise AssertionError("No-arbitrage-violating Heston delta was accepted")
        if "no_arbitrage_bound_violation" not in invalid.invalid_reasons:
            raise AssertionError("Expected exact no-arbitrage invalid reason")
        try:
            heston_delta_call(
                spot=100.0,
                strike=100.0,
                rate=0.01,
                div=0.0,
                T=1.0,
                params=params,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid Heston delta must fail closed, not clip")
    finally:
        delta_hedge_pnl.heston_call_price = original_pricer

    aggregate = delta_hedge_pnl.summarize_heston_delta_numerics(
        pd.DataFrame(
            {
                delta_hedge_pnl.HESTON_DELTA_EVALUATED_COL: [True, True],
                delta_hedge_pnl.HESTON_DELTA_VALID_COL: [True, False],
                delta_hedge_pnl.HESTON_DELTA_INVALID_REASON_COL: [
                    "",
                    "no_arbitrage_bound_violation",
                ],
                "quotes": [5, 3],
            }
        )
    )
    if aggregate["status"] != "invalid":
        raise AssertionError("Partial Heston delta validity must remain invalid")
    if aggregate["evaluated_surface_rows"] != 2:
        raise AssertionError("Heston delta evaluated-row count mismatch")
    if aggregate["invalid_surface_rows"] != 1:
        raise AssertionError("Heston delta invalid-row count mismatch")
    if aggregate["invalid_quote_weight"] != 3:
        raise AssertionError("Heston delta invalid quote weight mismatch")


def _assert_independent_heston_reference_grid() -> None:
    """Lock the analytic implementation to a separate QuantLib reference."""
    regimes = (
        (1.5, 0.04, 0.5, -0.7, 0.04),
        (0.5, 0.25, 1.5, -0.85, 0.25),
        (3.0, 0.02, 0.3, -0.3, 0.02),
    )
    max_price_abs_error = 0.0
    max_delta_abs_error = 0.0
    max_reference_bump_instability = 0.0
    for params in regimes:
        params_dict = dict(zip(("kappa", "theta", "sigma", "rho", "v0"), params))
        for ttm_years in (30.0 / 365.0, 182.0 / 365.0, 2.0):
            for strike in (80.0, 100.0, 120.0):
                inputs = {
                    "spot": 100.0,
                    "strike": strike,
                    "rate": 0.02,
                    "div": 0.01,
                    "T": ttm_years,
                }
                actual_price = heston_call_price(
                    **inputs,
                    params=params,
                    n_points=REFERENCE_QUADRATURE_POINTS,
                    laguerre_scale=REFERENCE_LAGUERRE_SCALE,
                )
                reference_price = quantlib_heston_call_price(
                    **inputs,
                    params=params,
                )
                actual_delta = delta_hedge_pnl.heston_delta_diagnostic(
                    **inputs,
                    params=params_dict,
                )
                reference_delta = quantlib_heston_delta(
                    **inputs,
                    params=params,
                )
                if not actual_delta.valid:
                    raise AssertionError(
                        "Reference-grid Heston delta failed closed: "
                        f"{actual_delta.invalid_reasons}"
                    )
                max_price_abs_error = max(
                    max_price_abs_error,
                    abs(actual_price - reference_price),
                )
                max_delta_abs_error = max(
                    max_delta_abs_error,
                    abs(actual_delta.candidate - reference_delta.value),
                )
                max_reference_bump_instability = max(
                    max_reference_bump_instability,
                    reference_delta.bump_stability_abs,
                )

    if max_price_abs_error > 1e-4:
        raise AssertionError(
            "Heston price exceeds independent QuantLib tolerance: "
            f"{max_price_abs_error:.12g}"
        )
    if max_delta_abs_error > 1e-5:
        raise AssertionError(
            "Heston delta exceeds independent QuantLib tolerance: "
            f"{max_delta_abs_error:.12g}"
        )
    if max_reference_bump_instability > 1e-5:
        raise AssertionError(
            "QuantLib reference delta is bump-unstable: "
            f"{max_reference_bump_instability:.12g}"
        )


def main() -> None:
    _assert_calibration_gate_unit_cases()
    _assert_independent_heston_reference_grid()
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "reproduce_wrds_local_metrics.sh"
    manifest = repo_root / "docs" / "artifacts" / "manifest.json"

    if not script.exists():
        raise FileNotFoundError(script)
    if not manifest.exists():
        raise FileNotFoundError(manifest)

    before_hash = _sha256(manifest)

    run_id = "wrds_local_ci_smoke"
    out_root = repo_root / "artifacts" / "_local" / "wrds_local" / run_id
    out_json = out_root / "metrics_export_sample.json"
    out_md = out_root / "metrics_export_sample.md"

    env = os.environ.copy()
    env["WRDS_USE_SAMPLE"] = "1"
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"
    cmd = [str(script), "--dateset", "wrds_pipeline_dates_panel.yaml", "--run-id", run_id]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        raise AssertionError(
            "Script failed with exit code "
            f"{result.returncode}. stdout={stdout!r} stderr={stderr!r}"
        )

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("Expected script to print metrics markdown path")
    printed = Path(lines[-1]).resolve()
    if printed != out_md.resolve():
        raise AssertionError(f"Expected printed path {out_md.resolve()}, got {printed}")

    if not out_json.exists():
        raise AssertionError(f"Missing metrics export JSON at {out_json}")
    if not out_md.exists():
        raise AssertionError(f"Missing metrics export Markdown at {out_md}")

    payload = json.loads(out_json.read_text())
    if "market_iv_bs_delta_pnl_sigma_median" not in payload["metrics"]["pnl"]:
        raise AssertionError("Renamed hedge sigma metric missing from local export")
    if "median_market_iv_bs_delta_pnl_sigma" not in payload["metrics"]["comparison"]:
        raise AssertionError("Renamed comparison hedge sigma metric missing from local export")
    if "median_calibrated_heston_delta_pnl_sigma" not in payload["metrics"]["comparison"]:
        raise AssertionError("Genuine Heston-delta hedge sigma missing from local export")
    claim_gate = payload.get("claim_gate", {})
    if claim_gate.get("status") not in {"diagnostic_only", "eligible"}:
        raise AssertionError("Sample claim gate returned an unknown status")

    fit_json = out_root / "per_date" / "2020-03-16" / "heston_fit.json"
    if not fit_json.exists():
        raise AssertionError(f"Missing fit diagnostics JSON at {fit_json}")
    fit_payload = json.loads(fit_json.read_text())
    diagnostics = fit_payload.get("calibration_diagnostics")
    if not isinstance(diagnostics, dict):
        raise AssertionError("calibration_diagnostics missing from fit summary")
    for key in [
        "success",
        "nfev",
        "cost",
        "optimality",
        "active_bound_count",
        "promotion_status",
        "minimum_normalized_boundary_distance",
        "multistart_count",
        "quadrature_points",
        "laguerre_scale",
        "price_output_clipped",
        "solver_coordinates",
    ]:
        if key not in diagnostics:
            raise AssertionError(f"Missing calibration_diagnostics.{key}")
    if diagnostics["solver_coordinates"] != "physical_bounded":
        raise AssertionError("Heston calibration did not use physical bounded coordinates")
    if diagnostics["price_output_clipped"] is not False:
        raise AssertionError("Heston calibration price clipping was re-enabled")
    if int(diagnostics["quadrature_points"]) < 96:
        raise AssertionError("Heston calibration quadrature regressed below 96 points")

    after_hash = _sha256(manifest)
    if after_hash != before_hash:
        raise AssertionError("docs/artifacts/manifest.json changed during local run")


if __name__ == "__main__":
    main()

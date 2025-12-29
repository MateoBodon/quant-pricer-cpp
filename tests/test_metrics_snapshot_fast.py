#!/usr/bin/env python3
"""FAST test: generate metrics snapshot from committed artifacts.

This test ensures the snapshot script runs and the outputs contain the
required top-level blocks with status fields, guarding against silent
schema drift in artifacts.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "docs" / "artifacts"
JSON_OUT = ARTIFACTS / "metrics_summary.json"
MD_OUT = ARTIFACTS / "metrics_summary.md"
CURRENT_RESULTS = REPO_ROOT / "project_state" / "CURRENT_RESULTS.md"


REQUIRED_KEYS = [
    "tri_engine_agreement",
    "qmc_vs_prng_equal_time",
    "pde_order",
    "ql_parity",
    "benchmarks",
    "wrds",
]


FLOAT_RE = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def run_snapshot() -> None:
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "generate_metrics_summary.py"),
        "--artifacts",
        str(ARTIFACTS),
        "--manifest",
        str(ARTIFACTS / "manifest.json"),
    ]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def assert_status_blocks(summary: Dict) -> None:
    metrics = summary.get("metrics")
    if not isinstance(metrics, dict):
        raise AssertionError("metrics key missing or not a dict")
    for key in REQUIRED_KEYS:
        if key not in metrics:
            raise AssertionError(f"missing metrics block: {key}")
        block = metrics[key]
        if "status" not in block:
            raise AssertionError(f"missing status in block {key}")
        if block["status"] not in {"ok", "missing", "parse_error"}:
            raise AssertionError(f"invalid status in block {key}: {block['status']}")


def _assert_close(label: str, actual: float, expected: float) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-8):
        raise AssertionError(
            f"{label} mismatch: current_results={actual} expected={expected}"
        )


def assert_current_results_matches_snapshot(summary: Dict) -> None:
    if not CURRENT_RESULTS.exists():
        raise AssertionError("CURRENT_RESULTS.md missing")
    text = CURRENT_RESULTS.read_text(encoding="utf-8")

    generated_at = summary.get("generated_at")
    manifest_sha = summary.get("manifest_git_sha")
    if not generated_at or generated_at not in text:
        raise AssertionError(
            f"CURRENT_RESULTS missing metrics_summary generated_at ({generated_at})"
        )
    if not manifest_sha or manifest_sha not in text:
        raise AssertionError(
            f"CURRENT_RESULTS missing manifest git SHA ({manifest_sha})"
        )
    if "docs/artifacts/metrics_summary.md" not in text:
        raise AssertionError("CURRENT_RESULTS missing metrics_summary path reference")

    tri_match = re.search(
        rf"Tri-engine agreement: max\|MC-BS\|=({FLOAT_RE}), "
        rf"max\|PDE-BS\|=({FLOAT_RE}), MC CI covers BS=(True|False)",
        text,
    )
    if not tri_match:
        raise AssertionError("CURRENT_RESULTS missing tri-engine highlight metrics")
    tri_mc = float(tri_match.group(1))
    tri_pde = float(tri_match.group(2))
    tri_covers = tri_match.group(3) == "True"

    qmc_match = re.search(
        rf"QMC vs PRNG: median RMSE ratio=({FLOAT_RE}) "
        rf"\(asian median=({FLOAT_RE}); call median=({FLOAT_RE})\)",
        text,
    )
    if not qmc_match:
        raise AssertionError("CURRENT_RESULTS missing QMC vs PRNG highlight metrics")
    qmc_overall = float(qmc_match.group(1))
    qmc_asian = float(qmc_match.group(2))
    qmc_call = float(qmc_match.group(3))

    bench_match = re.search(
        rf"Benchmarks: MC paths/sec \(1t\)=({FLOAT_RE}), eff@max=({FLOAT_RE})",
        text,
    )
    if not bench_match:
        raise AssertionError("CURRENT_RESULTS missing benchmark highlight metrics")
    bench_paths = float(bench_match.group(1))
    bench_eff = float(bench_match.group(2))

    wrds_match = re.search(rf"WRDS: median iv_rmse=({FLOAT_RE})", text)
    if not wrds_match:
        raise AssertionError("CURRENT_RESULTS missing WRDS highlight metrics")
    wrds_iv_rmse = float(wrds_match.group(1))

    pde_match = re.search(
        rf"PDE order: slope=({FLOAT_RE}), rmse_finest=({FLOAT_RE})", text
    )
    if not pde_match:
        raise AssertionError("CURRENT_RESULTS missing PDE order highlight metrics")
    pde_slope = float(pde_match.group(1))
    pde_rmse = float(pde_match.group(2))

    ql_match = re.search(
        rf"QL parity: max diff=({FLOAT_RE}) cents, median=({FLOAT_RE}) cents, "
        rf"p95=({FLOAT_RE}) cents",
        text,
    )
    if not ql_match:
        raise AssertionError("CURRENT_RESULTS missing QL parity highlight metrics")
    ql_max = float(ql_match.group(1))
    ql_median = float(ql_match.group(2))
    ql_p95 = float(ql_match.group(3))

    try:
        tri_metrics = summary["metrics"]["tri_engine_agreement"]["metrics"]
        pde_metrics = summary["metrics"]["pde_order"]["metrics"]
        ql_metrics = summary["metrics"]["ql_parity"]["metrics"]
        qmc_metrics = summary["metrics"]["qmc_vs_prng_equal_time"]["metrics"]
        bench_metrics = summary["metrics"]["benchmarks"]["mc_paths"]["metrics"]
        wrds_metrics = summary["metrics"]["wrds"]["pricing"]["metrics"]
    except KeyError as exc:
        raise AssertionError(f"metrics_summary missing expected keys: {exc}") from exc

    _assert_close(
        "tri_engine.max_abs_error_mc",
        tri_mc,
        float(tri_metrics["max_abs_error_mc"]),
    )
    _assert_close(
        "tri_engine.max_abs_error_pde",
        tri_pde,
        float(tri_metrics["max_abs_error_pde"]),
    )
    if tri_covers != bool(tri_metrics["mc_ci_covers_bs"]):
        raise AssertionError(
            "tri_engine.mc_ci_covers_bs mismatch: "
            f"current_results={tri_covers} expected={tri_metrics['mc_ci_covers_bs']}"
        )

    _assert_close(
        "qmc_vs_prng.rmse_ratio_overall_median",
        qmc_overall,
        float(qmc_metrics["rmse_ratio_overall_median"]),
    )
    _assert_close(
        "qmc_vs_prng.asian.rmse_ratio_median",
        qmc_asian,
        float(qmc_metrics["payoffs"]["asian"]["rmse_ratio_median"]),
    )
    _assert_close(
        "qmc_vs_prng.call.rmse_ratio_median",
        qmc_call,
        float(qmc_metrics["payoffs"]["call"]["rmse_ratio_median"]),
    )
    _assert_close(
        "benchmarks.paths_per_sec_1t",
        bench_paths,
        float(bench_metrics["paths_per_sec_1t"]),
    )
    _assert_close(
        "benchmarks.efficiency_max_threads",
        bench_eff,
        float(bench_metrics["efficiency_max_threads"]),
    )
    _assert_close(
        "wrds.median_iv_rmse_volpts_vega_wt",
        wrds_iv_rmse,
        float(wrds_metrics["median_iv_rmse_volpts_vega_wt"]),
    )
    _assert_close("pde_order.slope", pde_slope, float(pde_metrics["slope"]))
    _assert_close(
        "pde_order.rmse_finest", pde_rmse, float(pde_metrics["rmse_finest"])
    )
    _assert_close(
        "ql_parity.max_abs_diff_cents_overall",
        ql_max,
        float(ql_metrics["max_abs_diff_cents_overall"]),
    )
    _assert_close(
        "ql_parity.median_abs_diff_cents_overall",
        ql_median,
        float(ql_metrics["median_abs_diff_cents_overall"]),
    )
    _assert_close(
        "ql_parity.p95_abs_diff_cents_overall",
        ql_p95,
        float(ql_metrics["p95_abs_diff_cents_overall"]),
    )


def test_snapshot_outputs_exist_and_parse() -> None:
    if not JSON_OUT.exists() or not MD_OUT.exists():
        raise AssertionError("metrics_summary.* missing; run reproduce_all to regenerate")
    committed_summary = load_json(JSON_OUT)
    assert_current_results_matches_snapshot(committed_summary)
    run_snapshot()
    if not JSON_OUT.exists():
        raise AssertionError("metrics_summary.json not created")
    if not MD_OUT.exists():
        raise AssertionError("metrics_summary.md not created")
    summary = load_json(JSON_OUT)
    assert_status_blocks(summary)


if __name__ == "__main__":
    test_snapshot_outputs_exist_and_parse()

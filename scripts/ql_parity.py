#!/usr/bin/env python3
"""
Compare quant-pricer-cpp against QuantLib across vanilla, barrier, and American options.

Outputs:
  * CSV with per-scenario price differences (cents) and runtime deltas.
  * PNG summary with price parity and runtime comparisons.
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import QuantLib as ql
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run
from protocol_utils import (
    load_protocol_configs,
    record_protocol_manifest,
)


MONEYNESS_BUCKETS = [
    (0.0, 0.97, "lt_0p97"),
    (0.97, 1.03, "0p97_1p03"),
    (1.03, math.inf, "gt_1p03"),
]
TENOR_BUCKETS = [
    (0.0, 0.75, "short_le_0p75y"),
    (0.75, 1.5, "mid_0p75_1p50y"),
    (1.5, math.inf, "long_gt_1p50y"),
]
VOL_BUCKETS = [
    (0.0, 0.20, "low_le_0p20"),
    (0.20, 0.25, "mid_0p20_0p25"),
    (0.25, math.inf, "high_gt_0p25"),
]


def _find_quant_cli(override: str | None) -> Path:
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path
        raise SystemExit(f"quant_cli not found at {path}")
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "build" / "quant_cli",
        root / "build" / "Release" / "quant_cli",
        root / "build" / "RelWithDebInfo" / "quant_cli",
        root / "quant_cli",
        root / "build" / "quant_cli.exe",
        root / "quant_cli.exe",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    raise SystemExit("quant_cli binary not found (build the project first)")


def _maturity_date(eval_date: ql.Date, tenor: float) -> ql.Date:
    days = max(1, int(round(tenor * 365)))
    return eval_date + ql.Period(days, ql.Days)


def _build_process(
    spot: float, rate: float, dividend: float, vol: float, eval_date: ql.Date
) -> ql.BlackScholesMertonProcess:
    day_count = ql.Actual365Fixed()
    calendar = ql.NullCalendar()
    ql.Settings.instance().evaluationDate = eval_date
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
    rf = ql.YieldTermStructureHandle(ql.FlatForward(eval_date, rate, day_count))
    div = ql.YieldTermStructureHandle(ql.FlatForward(eval_date, dividend, day_count))
    vol_ts = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(eval_date, calendar, vol, day_count)
    )
    return ql.BlackScholesMertonProcess(spot_handle, div, rf, vol_ts)


@dataclass
class Scenario:
    name: str
    label: str
    kind: str  # vanilla, barrier, american
    params: Dict[str, float | int | str]


def _bucket(value: float, buckets: List[tuple[float, float, str]]) -> str:
    if not math.isfinite(value):
        return "unknown"
    for lower, upper, label in buckets:
        if lower <= value <= upper:
            return label
    return "out_of_range"


def _bucket_definitions() -> Dict[str, List[Dict[str, float | str]]]:
    def _format(entries: List[tuple[float, float, str]]) -> List[Dict[str, float | str]]:
        return [
            {"lower": lower, "upper": upper, "label": label} for lower, upper, label in entries
        ]

    return {
        "moneyness": _format(MONEYNESS_BUCKETS),
        "tenor_years": _format(TENOR_BUCKETS),
        "vol": _format(VOL_BUCKETS),
    }


def _parse_eval_date(value: str) -> ql.Date:
    try:
        year, month, day = (int(part) for part in value.split("-"))
    except Exception as exc:
        raise SystemExit(
            f"invalid ql_parity eval_date '{value}' (expected YYYY-MM-DD)"
        ) from exc
    return ql.Date(day, month, year)


def _scenarios_from_config(config: Dict[str, Any], fast: bool) -> List[Scenario]:
    block = config.get("ql_parity")
    if not isinstance(block, dict):
        raise SystemExit("scenario grid missing 'ql_parity' block")
    scenarios_raw = block.get("scenarios")
    if not isinstance(scenarios_raw, list):
        raise SystemExit("ql_parity.scenarios must be a list")
    scenarios = [
        Scenario(
            name=str(item.get("name")),
            label=str(item.get("label")),
            kind=str(item.get("kind")),
            params=dict(item.get("params", {})),
        )
        for item in scenarios_raw
    ]
    if fast:
        fast_names = block.get("fast_scenarios", [])
        if not fast_names:
            raise SystemExit("ql_parity.fast_scenarios missing for --fast")
        fast_set = {str(name) for name in fast_names}
        scenarios = [scenario for scenario in scenarios if scenario.name in fast_set]
        missing = fast_set - {scenario.name for scenario in scenarios}
        if missing:
            raise SystemExit(f"ql_parity.fast_scenarios not found: {sorted(missing)}")
    return scenarios


def _run_cli(quant_cli: Path, scenario: Scenario) -> tuple[float, float]:
    args: List[str] = []
    p = scenario.params
    if scenario.kind == "vanilla":
        args = [
            "bs",
            str(p["S"]),
            str(p["K"]),
            str(p["r"]),
            str(p["q"]),
            str(p["vol"]),
            str(p["T"]),
            str(p["type"]),
            "--json",
        ]
    elif scenario.kind == "barrier":
        args = [
            "barrier",
            "pde",
            str(p["type"]),
            str(p["direction"]),
            str(p["style"]),
            str(p["S"]),
            str(p["K"]),
            str(p["barrier"]),
            str(p["rebate"]),
            str(p["r"]),
            str(p["q"]),
            str(p["vol"]),
            str(p["T"]),
            str(int(p["space_nodes"])),
            str(int(p["time_steps"])),
            str(p["smax_mult"]),
            "--json",
        ]
    elif scenario.kind == "american":
        args = [
            "american",
            "psor",
            str(p["type"]),
            str(p["S"]),
            str(p["K"]),
            str(p["r"]),
            str(p["q"]),
            str(p["vol"]),
            str(p["T"]),
            str(int(p["space_nodes"])),
            str(int(p["time_steps"])),
            str(p["smax_mult"]),
            str(int(p["logspace"])),
            str(int(p["neumann"])),
            str(p["stretch"]),
            str(p["omega"]),
            str(int(p["max_iter"])),
            str(p["tol"]),
            "--json",
        ]
    else:
        raise ValueError(f"Unsupported scenario kind: {scenario.kind}")

    cmd = [str(quant_cli)] + args
    tic = perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    runtime_ms = (perf_counter() - tic) * 1_000.0
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to parse quant_cli output: {proc.stdout}") from exc
    price = float(payload["price"])
    return price, runtime_ms


def _price_quantlib(scenario: Scenario, eval_date: ql.Date) -> tuple[float, float]:
    p = scenario.params
    process = _build_process(
        float(p["S"]), float(p["r"]), float(p["q"]), float(p["vol"]), eval_date
    )
    payoff = ql.PlainVanillaPayoff(
        ql.Option.Call if str(p["type"]).lower() == "call" else ql.Option.Put,
        float(p["K"]),
    )
    maturity = _maturity_date(eval_date, float(p["T"]))
    tic = perf_counter()
    if scenario.kind == "vanilla":
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    elif scenario.kind == "barrier":
        style = (
            ql.Barrier.DownOut if str(p["direction"]) == "down" else ql.Barrier.UpOut
        )
        if str(p["style"]) == "in":
            style = (
                ql.Barrier.DownIn if str(p["direction"]) == "down" else ql.Barrier.UpIn
            )
        option = ql.BarrierOption(
            style,
            float(p["barrier"]),
            float(p["rebate"]),
            payoff,
            ql.EuropeanExercise(maturity),
        )
        option.setPricingEngine(ql.AnalyticBarrierEngine(process))
    elif scenario.kind == "american":
        exercise = ql.AmericanExercise(eval_date, maturity)
        option = ql.VanillaOption(payoff, exercise)
        option.setPricingEngine(
            ql.BinomialVanillaEngine(process, "crr", int(p["time_steps"]))
        )
    else:
        raise ValueError(f"Unsupported scenario kind: {scenario.kind}")
    price = option.NPV()
    runtime_ms = (perf_counter() - tic) * 1_000.0
    return price, runtime_ms


def _plot(df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.0), constrained_layout=True)
    colors = {
        "vanilla": "#1f77b4",
        "barrier": "#2ca02c",
        "american": "#d62728",
    }
    df_sorted = df.sort_values("category")
    axes[0].bar(
        df_sorted["label"],
        df_sorted["abs_diff_cents"],
        color=[colors.get(cat, "#7f7f7f") for cat in df_sorted["category"]],
    )
    axes[0].set_ylabel("|Δprice| (cents)")
    axes[0].set_title("QuantLib vs quant-pricer-cpp price parity")
    axes[0].grid(True, axis="y", linestyle=":", alpha=0.4)
    for idx, value in enumerate(df_sorted["abs_diff_cents"]):
        axes[0].text(idx, value, f"{value:.2f}¢", ha="center", va="bottom", fontsize=8)

    x = range(len(df_sorted))
    width = 0.35
    axes[1].bar(
        [i - width / 2 for i in x],
        df_sorted["runtime_ms_quant_pricer"],
        width=width,
        label="quant-pricer",
        color="#9467bd",
    )
    axes[1].bar(
        [i + width / 2 for i in x],
        df_sorted["runtime_ms_quantlib"],
        width=width,
        label="QuantLib",
        color="#8c564b",
    )
    axes[1].set_ylabel("Runtime (ms)")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(df_sorted["label"], rotation=20, ha="right")
    axes[1].set_title("Runtime comparison (lower is faster)")
    axes[1].grid(True, axis="y", linestyle=":", alpha=0.4)
    for i, row in enumerate(df_sorted.itertuples()):
        axes[1].text(
            i - width / 2,
            row.runtime_ms_quant_pricer,
            f"{row.runtime_ms_quant_pricer:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
        axes[1].text(
            i + width / 2,
            row.runtime_ms_quantlib,
            f"{row.runtime_ms_quantlib:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    axes[1].legend()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _plot_error_distribution(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(6.5, 4.5), constrained_layout=True)
    values = df["abs_diff_cents"].dropna().to_numpy(dtype=float)
    if len(values) == 0:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    else:
        bins = min(20, max(1, len(values)))
        ax.hist(values, bins=bins, color="#4c72b0", edgecolor="white")
    ax.set_xlabel("|Δprice| (cents)")
    ax.set_ylabel("Count")
    ax.set_title("QuantLib parity error distribution")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--quant-cli",
        default=None,
        help="Path to quant_cli (defaults to build/quant_cli)",
    )
    ap.add_argument(
        "--scenario-grid", type=Path, help="Path to frozen scenario grid JSON"
    )
    ap.add_argument(
        "--tolerances", type=Path, help="Path to frozen tolerance JSON"
    )
    ap.add_argument(
        "--output",
        default=str(ARTIFACTS_ROOT / "ql_parity" / "ql_parity.png"),
    )
    ap.add_argument(
        "--csv",
        default=str(ARTIFACTS_ROOT / "ql_parity" / "ql_parity.csv"),
    )
    ap.add_argument(
        "--bucket-summary",
        default=str(ARTIFACTS_ROOT / "ql_parity" / "ql_parity_bucket_summary.csv"),
    )
    ap.add_argument(
        "--error-dist",
        default=str(ARTIFACTS_ROOT / "ql_parity" / "ql_parity_error_dist.png"),
    )
    ap.add_argument(
        "--fast", action="store_true", help="Smaller scenario set for quicker iteration"
    )
    args = ap.parse_args()

    scenario_config, tolerance_config, provenance = load_protocol_configs(
        args.scenario_grid, args.tolerances
    )
    protocol_entry = record_protocol_manifest(
        scenario_config, tolerance_config, provenance
    )

    quant_cli = _find_quant_cli(args.quant_cli)
    scenarios = _scenarios_from_config(scenario_config, args.fast)
    eval_date_value = scenario_config.get("ql_parity", {}).get("eval_date", "2024-01-01")
    eval_date = _parse_eval_date(str(eval_date_value))

    rows: List[Dict[str, float | str]] = []
    for scenario in scenarios:
        price_cli, runtime_cli = _run_cli(quant_cli, scenario)
        price_ql, runtime_ql = _price_quantlib(scenario, eval_date)
        abs_diff = abs(price_cli - price_ql)
        diff_cents = abs_diff * 100.0
        rel_diff = abs_diff / price_ql if price_ql != 0 else math.nan
        runtime_ratio = runtime_cli / runtime_ql if runtime_ql > 0 else math.nan
        p = scenario.params
        spot = float(p["S"])
        strike = float(p["K"])
        tenor = float(p["T"])
        vol = float(p["vol"])
        moneyness = spot / strike if strike != 0 else math.nan
        bucket_row = {
            "moneyness_bucket": _bucket(moneyness, MONEYNESS_BUCKETS),
            "tenor_bucket": _bucket(tenor, TENOR_BUCKETS),
            "vol_bucket": _bucket(vol, VOL_BUCKETS),
        }
        rows.append(
            {
                "name": scenario.name,
                "label": scenario.label,
                "category": scenario.kind,
                "spot": spot,
                "strike": strike,
                "tenor": tenor,
                "vol": vol,
                "rate": float(p["r"]),
                "dividend": float(p["q"]),
                "moneyness": moneyness,
                **bucket_row,
                "price_quant_pricer": price_cli,
                "price_quantlib": price_ql,
                "abs_diff": abs_diff,
                "abs_diff_cents": diff_cents,
                "rel_diff": rel_diff,
                "runtime_ms_quant_pricer": runtime_cli,
                "runtime_ms_quantlib": runtime_ql,
                "runtime_ratio": runtime_ratio,
            }
        )

    df = pd.DataFrame(rows)
    out_csv = Path(args.csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, float_format="%.10f")
    out_png = Path(args.output)
    _plot(df, out_png)
    out_bucket = Path(args.bucket_summary)
    bucket_cols = ["category", "tenor_bucket", "moneyness_bucket", "vol_bucket"]
    bucket_metrics_cols = [
        "count",
        "max_abs_diff_cents",
        "median_abs_diff_cents",
        "p95_abs_diff_cents",
    ]
    if df.empty:
        bucket_summary = pd.DataFrame(columns=bucket_cols + bucket_metrics_cols)
    else:
        bucket_summary = (
            df.groupby(bucket_cols, dropna=False)["abs_diff_cents"]
            .agg(
                count="count",
                max_abs_diff_cents="max",
                median_abs_diff_cents="median",
                p95_abs_diff_cents=lambda series: series.quantile(0.95),
            )
            .reset_index()
        )
    out_bucket.parent.mkdir(parents=True, exist_ok=True)
    bucket_summary.to_csv(out_bucket, index=False, float_format="%.10f")
    out_error_dist = Path(args.error_dist)
    _plot_error_distribution(df, out_error_dist)

    tol = tolerance_config.get("ql_parity", {})
    max_abs_diff = float(df["abs_diff_cents"].max()) if not df.empty else math.nan
    diff_ok = None
    if "max_abs_diff_cents" in tol:
        diff_ok = max_abs_diff <= float(tol["max_abs_diff_cents"])

    update_run(
        "ql_parity",
        {
            "csv": str(out_csv),
            "figure": str(out_png),
            "bucket_summary_csv": str(out_bucket),
            "error_distribution_figure": str(out_error_dist),
            "quant_cli": str(quant_cli),
            "scenarios": [scenario.name for scenario in scenarios],
            "fast": bool(args.fast),
            "eval_date": eval_date.ISO(),
            "max_abs_diff_cents": max_abs_diff,
            "bucket_definitions": _bucket_definitions(),
            "protocol": protocol_entry,
            "tolerances": tol,
            "tolerance_checks": {"max_abs_diff_cents_ok": diff_ok},
            "inputs": describe_inputs([quant_cli, args.scenario_grid, args.tolerances]),
        },
        append=True,
    )
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_png}")
    print(f"Wrote {out_bucket}")
    print(f"Wrote {out_error_dist}")


if __name__ == "__main__":
    main()

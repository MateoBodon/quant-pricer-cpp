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
from typing import Callable, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import QuantLib as ql
from manifest_utils import ARTIFACTS_ROOT, update_run


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


def _scenarios(fast: bool) -> List[Scenario]:
    vanilla = [
        Scenario(
            name="vanilla_call_atm",
            label="Call ATM 6M",
            kind="vanilla",
            params=dict(
                type="call", S=100.0, K=100.0, r=0.02, q=0.005, vol=0.20, T=0.5
            ),
        ),
        Scenario(
            name="vanilla_put_otm",
            label="Put OTM 1.5y",
            kind="vanilla",
            params=dict(type="put", S=95.0, K=105.0, r=0.015, q=0.0, vol=0.25, T=1.5),
        ),
    ]
    barrier = [
        Scenario(
            name="barrier_do_call",
            label="Down-&-Out Call",
            kind="barrier",
            params=dict(
                type="call",
                direction="down",
                style="out",
                S=100.0,
                K=100.0,
                barrier=90.0,
                rebate=0.0,
                r=0.02,
                q=0.0,
                vol=0.22,
                T=1.0,
                space_nodes=241,
                time_steps=240,
                smax_mult=4.0,
            ),
        ),
    ]
    american = [
        Scenario(
            name="american_put_psor",
            label="American Put",
            kind="american",
            params=dict(
                type="put",
                S=95.0,
                K=100.0,
                r=0.03,
                q=0.01,
                vol=0.20,
                T=1.0,
                space_nodes=181,
                time_steps=180,
                smax_mult=4.0,
                logspace=1,
                neumann=1,
                stretch=2.0,
                omega=1.4,
                max_iter=6000,
                tol=1e-8,
            ),
        ),
    ]
    if fast:
        return [vanilla[0], barrier[0], american[0]]
    return vanilla + barrier + american


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--quant-cli",
        default=None,
        help="Path to quant_cli (defaults to build/quant_cli)",
    )
    ap.add_argument("--output", default="docs/artifacts/ql_parity/ql_parity.png")
    ap.add_argument("--csv", default="docs/artifacts/ql_parity/ql_parity.csv")
    ap.add_argument(
        "--fast", action="store_true", help="Smaller scenario set for quicker iteration"
    )
    args = ap.parse_args()

    quant_cli = _find_quant_cli(args.quant_cli)
    scenarios = _scenarios(args.fast)
    eval_date = ql.Date(1, ql.January, 2024)

    rows: List[Dict[str, float | str]] = []
    for scenario in scenarios:
        price_cli, runtime_cli = _run_cli(quant_cli, scenario)
        price_ql, runtime_ql = _price_quantlib(scenario, eval_date)
        diff_cents = abs(price_cli - price_ql) * 100.0
        runtime_ratio = runtime_cli / runtime_ql if runtime_ql > 0 else math.nan
        rows.append(
            {
                "name": scenario.name,
                "label": scenario.label,
                "category": scenario.kind,
                "price_quant_pricer": price_cli,
                "price_quantlib": price_ql,
                "abs_diff_cents": diff_cents,
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

    update_run(
        "ql_parity",
        {
            "csv": str(out_csv),
            "figure": str(out_png),
            "quant_cli": str(quant_cli),
            "scenarios": [scenario.name for scenario in scenarios],
            "fast": bool(args.fast),
        },
        append=True,
    )
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_png}")


if __name__ == "__main__":
    main()

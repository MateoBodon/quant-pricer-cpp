#!/usr/bin/env python3
"""
Generate Monte Carlo Greeks with 95% confidence intervals and persist CSV/PNG artifacts.
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run
from protocol_utils import (
    load_protocol_configs,
    record_protocol_manifest,
    select_grid_block,
)


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
        root / "build" / "Debug" / "quant_cli",
        root / "build" / "quant_cli.exe",
        root / "build" / "Release" / "quant_cli.exe",
        root / "quant_cli",
        root / "quant_cli.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit("quant_cli executable not found; pass --quant-cli")


def _run_cli_json(cli: Path, args: List[str]) -> Dict[str, Any]:
    cmd = [str(cli), *[str(arg) for arg in args]]
    output = subprocess.check_output(cmd, text=True)
    return json.loads(output)


def _confidence_band(std_error: float) -> float:
    return 1.96 * std_error


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quant-cli", help="Path to quant_cli executable")
    ap.add_argument(
        "--fast", action="store_true", help="Halve the number of paths for CI pipelines"
    )
    ap.add_argument(
        "--scenario-grid", type=Path, help="Path to frozen scenario grid JSON"
    )
    ap.add_argument(
        "--tolerances", type=Path, help="Path to frozen tolerance JSON"
    )
    ap.add_argument(
        "--output",
        default=str(ARTIFACTS_ROOT / "mc_greeks_ci.png"),
        help="Figure output path",
    )
    ap.add_argument(
        "--csv",
        default=str(ARTIFACTS_ROOT / "mc_greeks_ci.csv"),
        help="CSV output path",
    )
    args = ap.parse_args()

    scenario_config, tolerance_config, provenance = load_protocol_configs(
        args.scenario_grid, args.tolerances
    )
    protocol_entry = record_protocol_manifest(
        scenario_config, tolerance_config, provenance
    )
    grid = select_grid_block(scenario_config, "mc_greeks_ci", args.fast)

    paths = int(grid["paths"])
    steps = int(grid["steps"])
    seed = int(grid["seed"])
    cli = _find_quant_cli(args.quant_cli)

    market = {
        "spot": float(grid["spot"]),
        "strike": float(grid["strike"]),
        "rate": float(grid["rate"]),
        "dividend": float(grid["dividend"]),
        "vol": float(grid["vol"]),
        "tenor": float(grid["tenor"]),
    }

    cmd = [
        "mc",
        market["spot"],
        market["strike"],
        market["rate"],
        market["dividend"],
        market["vol"],
        market["tenor"],
        paths,
        seed,
        1,
        "none",
        "none",
        steps,
        "--greeks",
        "--ci",
        "--rng=counter",
        "--json",
    ]
    result = _run_cli_json(cli, cmd)
    greeks = result.get("greeks", {})
    if not greeks:
        raise SystemExit(
            "quant_cli did not return Greeks payload; ensure build enables Greeks"
        )

    records = []
    ordering = [
        ("delta", "Delta"),
        ("vega", "Vega"),
        ("gamma_lrm", "Gamma (LRM)"),
        ("gamma_pathwise", "Gamma (pathwise)"),
        ("theta", "Theta"),
    ]
    for key, label in ordering:
        stats = greeks.get(key)
        if not stats:
            continue
        records.append(
            {
                "greek": label,
                "estimate": float(stats.get("value", 0.0)),
                "std_error": float(stats.get("std_error", 0.0)),
                "ci_low": float(stats.get("ci_low", 0.0)),
                "ci_high": float(stats.get("ci_high", 0.0)),
            }
        )

    if not records:
        raise SystemExit("No Greeks were recorded in CLI output")

    df = pd.DataFrame(records)
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.8f")

    fig_path = Path(args.output)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ci = [2.0 * _confidence_band(err) for err in df["std_error"]]
    ax.bar(df["greek"], df["estimate"], yerr=ci, capsize=6, color="#1f77b4")
    ax.axhline(0.0, color="#444444", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_ylabel("Estimate")
    ax.set_title(f"MC Greeks ±95% CI (paths={paths:,}, seed={seed})")
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180)
    plt.close(fig)

    tol = tolerance_config.get("mc_greeks_ci", {})
    max_std_error = float(df["std_error"].max())
    std_error_ok = None
    if "max_std_error" in tol:
        std_error_ok = max_std_error <= float(tol["max_std_error"])

    payload = {
        "command": shlex.join([str(cli), *[str(arg) for arg in cmd]]),
        "paths": paths,
        "seed": seed,
        "steps": steps,
        "rng": "counter",
        "antithetic": True,
        "csv": str(csv_path),
        "figure": str(fig_path),
        "records": records,
        "price": float(result.get("price", math.nan)),
        "std_error": float(result.get("std_error", math.nan)),
        "max_std_error": max_std_error,
        "protocol": protocol_entry,
        "tolerances": tol,
        "tolerance_checks": {"max_std_error_ok": std_error_ok},
        "inputs": describe_inputs([cli, args.scenario_grid, args.tolerances]),
    }
    update_run("mc_greeks_ci", payload)

    print(f"Wrote {csv_path}")
    print(f"Wrote {fig_path}")


if __name__ == "__main__":
    main()

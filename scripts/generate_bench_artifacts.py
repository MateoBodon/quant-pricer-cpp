#!/usr/bin/env python3
"""
Convert Google Benchmark JSON into CSV + plots + manifest entries.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import update_run


def load_benchmarks(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("benchmarks", [])


def parse_mc(
    benches: List[Dict[str, Any]]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    throughput_rows: List[Dict[str, Any]] = []
    rmse_rows: List[Dict[str, Any]] = []
    equal_rows: List[Dict[str, Any]] = []
    for bench in benches:
        name: str = bench["name"]
        real_time_ms = float(bench.get("real_time", 0.0)) / 1e6
        if name.startswith("BM_MC_PathsPerSecond"):
            _, threads_str = name.split("/")
            throughput_rows.append(
                {
                    "threads": int(threads_str),
                    "paths_per_sec": float(bench.get("paths/s", 0.0)),
                }
            )
        elif "Rmse_PRNG" in name:
            rmse_rows.append(
                {"method": "PRNG", "std_error": float(bench.get("std_error", 0.0))}
            )
        elif "Rmse_QMC" in name:
            rmse_rows.append(
                {"method": "QMC", "std_error": float(bench.get("std_error", 0.0))}
            )
        elif name.startswith("BM_MC_EqualTime"):
            parts = name.split("/")
            if len(parts) == 3:
                equal_rows.append(
                    {
                        "payoff": parts[1],
                        "method": parts[2],
                        "std_error": float(bench.get("std_error", 0.0)),
                        "real_time_ms": real_time_ms,
                    }
                )
    throughput_df = pd.DataFrame(throughput_rows).sort_values("threads")
    if not throughput_df.empty:
        base = max(float(throughput_df["paths_per_sec"].iloc[0]), 1e-9)
        throughput_df["speedup"] = throughput_df["paths_per_sec"] / base
        throughput_df["efficiency"] = (
            throughput_df["speedup"] / throughput_df["threads"]
        )
    rmse_df = pd.DataFrame(rmse_rows)
    equal_df = pd.DataFrame(equal_rows)
    if not equal_df.empty:
        equal_df["time_scaled_error"] = equal_df["std_error"] * np.sqrt(
            equal_df["real_time_ms"].clip(lower=1e-9)
        )
    return throughput_df, rmse_df, equal_df


def parse_pde(
    benches: List[Dict[str, Any]]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    wall_rows: List[Dict[str, Any]] = []
    psor_rows: List[Dict[str, Any]] = []
    order_rows: List[Dict[str, Any]] = []
    for bench in benches:
        name: str = bench["name"]
        real_time_ms = float(bench.get("real_time", 0.0)) / 1e6
        if name.startswith("BM_PDE_WallTime"):
            _, m_str, _ = name.split("/")
            wall_rows.append(
                {
                    "space_nodes": int(m_str),
                    "real_time_ms": float(bench.get("real_time", 0.0)) / 1e6,
                    "price": float(bench.get("price", 0.0)),
                }
            )
        elif name.startswith("BM_PSOR_Iterations"):
            _, omega_str = name.split("/")
            psor_rows.append(
                {
                    "omega": int(omega_str) / 100.0,
                    "iterations": float(bench.get("iterations", 0.0)),
                    "residual": float(bench.get("residual", 0.0)),
                }
            )
        elif name.startswith("BM_PDE_OrderSlope"):
            _, m_str, _ = name.split("/")
            order_rows.append(
                {
                    "space_nodes": int(m_str),
                    "real_time_ms": real_time_ms,
                    "abs_error": float(bench.get("abs_error", 0.0)),
                }
            )
    wall_df = pd.DataFrame(wall_rows).sort_values("space_nodes")
    psor_df = pd.DataFrame(psor_rows).sort_values("omega")
    order_df = pd.DataFrame(order_rows).sort_values("space_nodes")
    return wall_df, psor_df, order_df


def plot_throughput(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.3))
    ax.plot(
        df["threads"],
        df["paths_per_sec"] / 1e6,
        marker="o",
        color="#1f77b4",
        label="Measured",
    )
    if not df.empty:
        base_threads = float(df["threads"].iloc[0])
        base_val = float(df["paths_per_sec"].iloc[0]) / 1e6
        ideal = base_val * (df["threads"] / base_threads)
        ax.plot(
            df["threads"], ideal, linestyle="--", color="#949494", label="Ideal linear"
        )
    ax.set_xlabel("Threads")
    ax.set_ylabel("Paths / sec (millions)")
    ax.set_title("Monte Carlo Throughput (OpenMP)")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()
    if "speedup" in df.columns:
        for _, row in df.iterrows():
            ax.text(
                row["threads"],
                row["paths_per_sec"] / 1e6,
                f"{row['speedup']:.1f}×",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_rmse(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.bar(df["method"], df["std_error"], color=["#d62728", "#2ca02c"])
    ax.set_ylabel("Std error")
    ax.set_title("MC RMSE (PRNG vs QMC)")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_equal_time(df: pd.DataFrame, out_path: Path) -> None:
    if df.empty:
        return
    payoffs = sorted(df["payoff"].unique())
    fig, axes = plt.subplots(
        1, len(payoffs), figsize=(6.0 * len(payoffs), 3.5), squeeze=False
    )
    colors = {"PRNG": "#d62728", "QMC": "#2ca02c"}
    for ax, payoff in zip(axes[0], payoffs):
        subset = df[df["payoff"] == payoff].set_index("method").reindex(["PRNG", "QMC"])
        metric = (
            "time_scaled_error"
            if "time_scaled_error" in subset.columns
            else "std_error"
        )
        values = subset[metric]
        bars = ax.bar(
            values.index,
            values.fillna(0.0),
            color=[colors.get(m, "#1f77b4") for m in values.index],
        )
        improvement_text = ""
        if (
            "PRNG" in subset.index
            and "QMC" in subset.index
            and subset[metric].notna().all()
        ):
            prng = float(subset.at["PRNG", metric])
            qmc = float(subset.at["QMC", metric])
            if prng > 0:
                improvement = 100.0 * (1.0 - qmc / prng)
                improvement_text = f" (QMC {improvement:+.1f}% better @ equal time)"
        ax.set_title(f"{payoff}{improvement_text}")
        ax.set_ylabel("σ · √ms" if ax is axes[0][0] else "")
        ax.grid(True, axis="y", linestyle=":", alpha=0.4)
        for method, bar in zip(values.index, bars):
            runtime = subset.at[method, "real_time_ms"]
            sigma = subset.at[method, "std_error"]
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height(),
                f"{sigma:.3e} σ\n{runtime:.0f} ms",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    axes[0][0].set_ylabel("Time-scaled RMSE (σ·√ms)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_walltime(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.plot(df["space_nodes"], df["real_time_ms"], marker="o", color="#9467bd")
    ax.set_xlabel("Spatial nodes")
    ax.set_ylabel("Wall time (ms)")
    ax.set_title("PDE Wall Time vs Grid Size")
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_psor(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.plot(df["omega"], df["iterations"], marker="o", color="#8c564b")
    ax.set_xlabel("ω (relaxation)")
    ax.set_ylabel("Iterations")
    ax.set_title("PSOR Iterations vs ω")
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_order(df: pd.DataFrame, out_path: Path) -> None:
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(5.0, 3.3))
    x = df["space_nodes"].to_numpy(dtype=float)
    y = df["abs_error"].to_numpy(dtype=float)
    ax.loglog(x, y, marker="o", color="#ff7f0e", label="Measured")
    if len(x) >= 2:
        slope, intercept = np.polyfit(np.log(x), np.log(y), 1)
        ref = y[0] * (x / x[0]) ** -2
        ax.loglog(x, ref, linestyle="--", color="#7f7f7f", label="-2 slope ref")
        ax.text(
            x[-1],
            y[-1],
            f"slope={slope:.2f}",
            fontsize=8,
            ha="right",
            va="bottom",
        )
    ax.set_xlabel("Spatial nodes")
    ax.set_ylabel("Abs error")
    ax.set_title("PDE convergence (log-log)")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc-json", default="docs/artifacts/bench/bench_mc.json")
    ap.add_argument("--pde-json", default="docs/artifacts/bench/bench_pde.json")
    ap.add_argument("--out-dir", default="docs/artifacts/bench")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mc_json = Path(args.mc_json)
    pde_json = Path(args.pde_json)

    throughput_df, rmse_df, equal_df = parse_mc(load_benchmarks(mc_json))
    wall_df, psor_df, order_df = parse_pde(load_benchmarks(pde_json))

    throughput_csv = out_dir / "bench_mc_paths.csv"
    rmse_csv = out_dir / "bench_mc_rmse.csv"
    wall_csv = out_dir / "bench_pde_walltime.csv"
    psor_csv = out_dir / "bench_psor_iterations.csv"
    equal_csv = out_dir / "bench_mc_equal_time.csv"
    order_csv = out_dir / "bench_pde_order.csv"

    throughput_df.to_csv(throughput_csv, index=False)
    rmse_df.to_csv(rmse_csv, index=False)
    wall_df.to_csv(wall_csv, index=False)
    psor_df.to_csv(psor_csv, index=False)
    equal_df.to_csv(equal_csv, index=False)
    order_df.to_csv(order_csv, index=False)

    plot_throughput(throughput_df, out_dir / "bench_mc_paths.png")
    plot_rmse(rmse_df, out_dir / "bench_mc_rmse.png")
    plot_equal_time(equal_df, out_dir / "bench_mc_equal_time.png")
    plot_walltime(wall_df, out_dir / "bench_pde_walltime.png")
    plot_psor(psor_df, out_dir / "bench_psor_iterations.png")
    plot_order(order_df, out_dir / "bench_pde_order.png")

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mc_json": str(mc_json),
        "pde_json": str(pde_json),
        "csv": [
            str(throughput_csv),
            str(rmse_csv),
            str(wall_csv),
            str(psor_csv),
            str(equal_csv),
            str(order_csv),
        ],
        "figures": [
            str(out_dir / "bench_mc_paths.png"),
            str(out_dir / "bench_mc_rmse.png"),
            str(out_dir / "bench_pde_walltime.png"),
            str(out_dir / "bench_psor_iterations.png"),
            str(out_dir / "bench_mc_equal_time.png"),
            str(out_dir / "bench_pde_order.png"),
        ],
    }
    update_run("benchmarks", payload, append=True, id_field="timestamp")

    print(f"Wrote {throughput_csv}, {rmse_csv}, {wall_csv}, {psor_csv}")
    print(f"Wrote plots under {out_dir}")


if __name__ == "__main__":
    main()

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
import pandas as pd

from manifest_utils import update_run


def load_benchmarks(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("benchmarks", [])


def parse_mc(benches: List[Dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    throughput_rows: List[Dict[str, Any]] = []
    rmse_rows: List[Dict[str, Any]] = []
    for bench in benches:
        name: str = bench["name"]
        counters: Dict[str, Any] = bench.get("counters", {})
        if name.startswith("BM_MC_PathsPerSecond"):
            _, threads_str = name.split("/")
            throughput_rows.append(
                {
                    "threads": int(threads_str),
                    "paths_per_sec": float(counters.get("paths/s", 0.0)),
                }
            )
        elif "Rmse_PRNG" in name:
            rmse_rows.append(
                {"method": "PRNG", "std_error": float(counters.get("std_error", 0.0))}
            )
        elif "Rmse_QMC" in name:
            rmse_rows.append(
                {"method": "QMC", "std_error": float(counters.get("std_error", 0.0))}
            )
    throughput_df = pd.DataFrame(throughput_rows).sort_values("threads")
    rmse_df = pd.DataFrame(rmse_rows)
    return throughput_df, rmse_df


def parse_pde(benches: List[Dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    wall_rows: List[Dict[str, Any]] = []
    psor_rows: List[Dict[str, Any]] = []
    for bench in benches:
        name: str = bench["name"]
        counters: Dict[str, Any] = bench.get("counters", {})
        if name.startswith("BM_PDE_WallTime"):
            _, m_str, _ = name.split("/")
            wall_rows.append(
                {
                    "space_nodes": int(m_str),
                    "real_time_ms": float(bench.get("real_time", 0.0)) / 1e6,
                    "price": float(counters.get("price", 0.0)),
                }
            )
        elif name.startswith("BM_PSOR_Iterations"):
            _, omega_str = name.split("/")
            psor_rows.append(
                {
                    "omega": int(omega_str) / 100.0,
                    "iterations": float(counters.get("iterations", 0.0)),
                    "residual": float(counters.get("residual", 0.0)),
                }
            )
    wall_df = pd.DataFrame(wall_rows).sort_values("space_nodes")
    psor_df = pd.DataFrame(psor_rows).sort_values("omega")
    return wall_df, psor_df


def plot_throughput(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.plot(df["threads"], df["paths_per_sec"] / 1e6, marker="o", color="#1f77b4")
    ax.set_xlabel("Threads")
    ax.set_ylabel("Paths / sec (millions)")
    ax.set_title("MC Throughput vs Threads")
    ax.grid(True, linestyle=":", alpha=0.5)
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

    throughput_df, rmse_df = parse_mc(load_benchmarks(mc_json))
    wall_df, psor_df = parse_pde(load_benchmarks(pde_json))

    throughput_csv = out_dir / "bench_mc_paths.csv"
    rmse_csv = out_dir / "bench_mc_rmse.csv"
    wall_csv = out_dir / "bench_pde_walltime.csv"
    psor_csv = out_dir / "bench_psor_iterations.csv"

    throughput_df.to_csv(throughput_csv, index=False)
    rmse_df.to_csv(rmse_csv, index=False)
    wall_df.to_csv(wall_csv, index=False)
    psor_df.to_csv(psor_csv, index=False)

    plot_throughput(throughput_df, out_dir / "bench_mc_paths.png")
    plot_rmse(rmse_df, out_dir / "bench_mc_rmse.png")
    plot_walltime(wall_df, out_dir / "bench_pde_walltime.png")
    plot_psor(psor_df, out_dir / "bench_psor_iterations.png")

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mc_json": str(mc_json),
        "pde_json": str(pde_json),
        "csv": [
            str(throughput_csv),
            str(rmse_csv),
            str(wall_csv),
            str(psor_csv),
        ],
        "figures": [
            str(out_dir / "bench_mc_paths.png"),
            str(out_dir / "bench_mc_rmse.png"),
            str(out_dir / "bench_pde_walltime.png"),
            str(out_dir / "bench_psor_iterations.png"),
        ],
    }
    update_run("benchmarks", payload, append=True, id_field="timestamp")

    print(f"Wrote {throughput_csv}, {rmse_csv}, {wall_csv}, {psor_csv}")
    print(f"Wrote plots under {out_dir}")


if __name__ == "__main__":
    main()

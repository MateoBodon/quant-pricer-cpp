#!/usr/bin/env python3
"""
Assess Monte Carlo Greek estimator reliability under GBM.

Compares pathwise, likelihood-ratio, and finite-difference estimators for Delta
and Gamma over an increasing number of simulated paths. Outputs:

  * docs/artifacts/greeks_reliability.csv — table with estimates and standard errors
  * docs/artifacts/greeks_reliability.png — micro-figure (StdErr vs N, log axes)
"""
from __future__ import annotations

import argparse
import math
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from manifest_utils import ARTIFACTS_ROOT, describe_inputs, update_run


@dataclass(frozen=True)
class McSpec:
    spot: float = 100.0
    strike: float = 100.0
    rate: float = 0.015
    dividend: float = 0.0
    vol: float = 0.20
    time: float = 0.5
    bump: float = 0.01


def _delta_pathwise(
    st: np.ndarray, payoff_mask: np.ndarray, spec: McSpec, discount: float
) -> np.ndarray:
    return discount * payoff_mask * (st / spec.spot)


def _delta_lr(
    payoff: np.ndarray, z: np.ndarray, spec: McSpec, discount: float
) -> np.ndarray:
    return discount * payoff * (z / (spec.spot * spec.vol * math.sqrt(spec.time)))


def _delta_fd(
    payoff_up: np.ndarray, payoff_dn: np.ndarray, spec: McSpec, discount: float
) -> np.ndarray:
    return discount * (payoff_up - payoff_dn) / (2.0 * spec.spot * spec.bump)


def _gamma_lr(
    payoff: np.ndarray, z: np.ndarray, spec: McSpec, discount: float
) -> np.ndarray:
    denom = (spec.spot * spec.vol) ** 2 * spec.time
    return discount * payoff * ((z * z - 1.0) / denom)


def _gamma_fd(
    payoff_up: np.ndarray,
    payoff: np.ndarray,
    payoff_dn: np.ndarray,
    spec: McSpec,
    discount: float,
) -> np.ndarray:
    denom = (spec.spot * spec.bump) ** 2
    return discount * (payoff_up - 2.0 * payoff + payoff_dn) / denom


def _simulate(
    n_paths: int,
    rng: np.random.Generator,
    spec: McSpec,
) -> Dict[str, np.ndarray]:
    z = rng.standard_normal(n_paths)
    drift = (spec.rate - spec.dividend - 0.5 * spec.vol * spec.vol) * spec.time
    diffusion = spec.vol * math.sqrt(spec.time) * z
    s_terminal = spec.spot * np.exp(drift + diffusion)

    spot_up = spec.spot * (1.0 + spec.bump)
    spot_dn = spec.spot * (1.0 - spec.bump)
    st_up = spot_up * np.exp(drift + diffusion)
    st_dn = spot_dn * np.exp(drift + diffusion)

    payoff = np.maximum(s_terminal - spec.strike, 0.0)
    payoff_up = np.maximum(st_up - spec.strike, 0.0)
    payoff_dn = np.maximum(st_dn - spec.strike, 0.0)
    discount = math.exp(-spec.rate * spec.time)
    itm_mask = (s_terminal > spec.strike).astype(float)

    samples = {
        "delta_pathwise": _delta_pathwise(s_terminal, itm_mask, spec, discount),
        "delta_lr": _delta_lr(payoff, z, spec, discount),
        "delta_fd": _delta_fd(payoff_up, payoff_dn, spec, discount),
        "gamma_lr": _gamma_lr(payoff, z, spec, discount),
        "gamma_fd": _gamma_fd(payoff_up, payoff, payoff_dn, spec, discount),
    }
    return samples


def _summaries(n_paths: int, samples: Dict[str, np.ndarray]) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for key, values in samples.items():
        greek = "delta" if key.startswith("delta") else "gamma"
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1))
        stderr = std / math.sqrt(n_paths)
        rows.append(
            {
                "N": int(n_paths),
                "method": key,
                "greek": greek,
                "estimate": mean,
                "std_error": stderr,
                "variance": std * std,
            }
        )
    return rows


def _plot(df: pd.DataFrame, output_png: Path) -> None:
    if df.empty:
        raise ValueError("No data to plot for Greeks reliability.")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for ax, greek in zip(axes, ["delta", "gamma"]):
        subset = df[df["greek"] == greek]
        for method, frame in subset.groupby("method"):
            frame = frame.sort_values("N")
            ax.loglog(
                frame["N"],
                frame["std_error"],
                marker="o",
                linewidth=1.5,
                label=method.replace("_", " "),
            )
        ax.set_title(f"{greek.capitalize()} estimator std. error")
        ax.set_xlabel("Paths (N)")
        ax.set_ylabel("Std error")
        ax.grid(which="both", linestyle="--", linewidth=0.6, alpha=0.4)
        ax.legend(fontsize=7)
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=180)
    plt.close(fig)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Monte Carlo Greeks reliability sweep.")
    ap.add_argument(
        "--fast", action="store_true", help="Use a short path grid for CI/PR workflows."
    )
    ap.add_argument(
        "--paths",
        nargs="*",
        type=int,
        default=[],
        help="Custom list of path counts (overrides --fast defaults).",
    )
    ap.add_argument(
        "--seed", type=int, default=2024, help="RNG seed for reproducibility."
    )
    ap.add_argument(
        "--output-csv", default=str(ARTIFACTS_ROOT / "greeks_reliability.csv")
    )
    ap.add_argument(
        "--output-png", default=str(ARTIFACTS_ROOT / "greeks_reliability.png")
    )
    ap.add_argument(
        "--skip-manifest", action="store_true", help="Suppress manifest logging."
    )
    return ap.parse_args()


def _path_grid(args: argparse.Namespace) -> Iterable[int]:
    if args.paths:
        return args.paths
    if args.fast:
        return [1_000, 2_000, 5_000, 10_000, 20_000]
    return [2_000, 5_000, 10_000, 20_000, 40_000, 80_000]


def main() -> None:
    args = _parse_args()
    spec = McSpec()
    rng = np.random.default_rng(args.seed)
    rows: List[Dict[str, float]] = []
    for n_paths in _path_grid(args):
        samples = _simulate(n_paths, rng, spec)
        rows.extend(_summaries(n_paths, samples))

    df = pd.DataFrame(rows).sort_values(["greek", "method", "N"])
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, float_format="%.8f")

    output_png = Path(args.output_png)
    _plot(df, output_png)

    command = shlex.join([sys.executable] + sys.argv)
    manifest_entry = {
        "command": command,
        "seed": args.seed,
        "fast": bool(args.fast),
        "paths": list(_path_grid(args)),
        "spec": spec.__dict__,
        "output_csv": str(output_csv),
        "output_png": str(output_png),
        "rows": len(df),
    }
    if not args.skip_manifest:
        update_run("greeks_reliability", manifest_entry)

    print(f"Saved Greeks reliability CSV -> {output_csv}")
    print(f"Saved Greeks reliability figure -> {output_png}")


if __name__ == "__main__":
    main()

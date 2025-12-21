#!/usr/bin/env python3
"""
Build a single source of truth for headline metrics directly from committed
artifacts. The script is intentionally defensive: if an artifact is missing or
its schema shifts, the corresponding block is marked `missing` or
`parse_error`, and the script exits non-zero after emitting actionable errors.

Outputs (default paths under docs/artifacts/):
  - metrics_summary.json (structured, machine-readable)
  - metrics_summary.md (human-readable, rendered from the JSON)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from manifest_utils import ARTIFACTS_ROOT, MANIFEST_PATH, describe_inputs, load_manifest, update_run

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------- Required artifacts ----------


@dataclass(frozen=True)
class RequiredArtifact:
    name: str
    relative_path: Path
    kind: str = "csv"  # csv, json, or file
    required_columns: Tuple[str, ...] = ()
    required_keys: Tuple[str, ...] = ()


REQUIRED_ARTIFACTS: Tuple[RequiredArtifact, ...] = (
    RequiredArtifact(
        name="tri_engine_agreement",
        relative_path=Path("tri_engine_agreement.csv"),
        required_columns=("bs_price", "mc_price", "pde_price"),
    ),
    RequiredArtifact(
        name="qmc_vs_prng_equal_time",
        relative_path=Path("qmc_vs_prng_equal_time.csv"),
        required_columns=("payoff", "rmse_ratio"),
    ),
    RequiredArtifact(
        name="pde_order_slope",
        relative_path=Path("pde_order_slope.csv"),
        required_columns=("nodes", "abs_error"),
    ),
    RequiredArtifact(
        name="ql_parity",
        relative_path=Path("ql_parity") / "ql_parity.csv",
        required_columns=("category", "abs_diff_cents"),
    ),
    RequiredArtifact(
        name="bench_mc_paths",
        relative_path=Path("bench") / "bench_mc_paths.csv",
        required_columns=("threads", "paths_per_sec"),
    ),
    RequiredArtifact(
        name="bench_mc_equal_time",
        relative_path=Path("bench") / "bench_mc_equal_time.csv",
        required_columns=("payoff", "method", "time_scaled_error"),
    ),
    RequiredArtifact(
        name="wrds_agg_pricing",
        relative_path=Path("wrds") / "wrds_agg_pricing.csv",
        required_columns=(
            "iv_rmse_volpts_vega_wt",
            "iv_mae_volpts_vega_wt",
            "price_rmse_ticks",
            "iv_mae_bps",
            "price_mae_ticks",
        ),
    ),
    RequiredArtifact(
        name="wrds_agg_oos",
        relative_path=Path("wrds") / "wrds_agg_oos.csv",
        required_columns=("iv_mae_bps", "price_mae_ticks"),
    ),
    RequiredArtifact(
        name="wrds_agg_pnl",
        relative_path=Path("wrds") / "wrds_agg_pnl.csv",
        required_columns=("mean_ticks", "mean_pnl", "pnl_sigma"),
    ),
)

REQUIRED_ARTIFACTS_BY_NAME: Dict[str, RequiredArtifact] = {item.name: item for item in REQUIRED_ARTIFACTS}


# ---------- Helpers ----------


def _safe_load_csv(path: Path) -> Tuple[pd.DataFrame | None, str | None]:
    if not path.exists():
        return None, "file not found"
    try:
        return pd.read_csv(path), None
    except Exception as exc:  # pragma: no cover - defensive guard
        return None, str(exc)


def _rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def _status_block(
    status: str,
    source: Path,
    metrics: Dict[str, Any] | None = None,
    reason: str | None = None,
    notes: List[str] | None = None,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "status": status,
        "source": _rel_path(source),
    }
    if metrics is not None:
        block["metrics"] = metrics
    if reason:
        block["reason"] = reason
    if notes:
        block["notes"] = notes
    return block


def _weighted_average(values: pd.Series, weights: pd.Series | None) -> float | None:
    if weights is None or weights.empty or weights.shape != values.shape:
        return float(values.mean()) if len(values) else None
    weight_sum = float(np.sum(weights))
    if weight_sum <= 0:
        return float(values.mean()) if len(values) else None
    return float(np.sum(values * weights) / weight_sum)


def _regression_slope(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Return (slope, r2) for y ~ a*x + b using least squares."""

    coeffs, residuals, _, _, _ = np.polyfit(x, y, 1, full=True)
    slope, intercept = coeffs
    pred = slope * x + intercept
    ss_res = float(residuals[0]) if len(residuals) else float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(slope), float(r2)


def _required_artifact(name: str) -> RequiredArtifact:
    try:
        return REQUIRED_ARTIFACTS_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"Required artifact not registered: {name}") from exc


def _required_path(name: str, artifacts_root: Path) -> Path:
    return artifacts_root / _required_artifact(name).relative_path


def _validate_required_artifacts(artifacts_root: Path) -> List[str]:
    errors: List[str] = []
    for req in REQUIRED_ARTIFACTS:
        path = artifacts_root / req.relative_path
        if not path.exists():
            hint = f"expected {req.kind}"
            if req.required_columns:
                hint += f" with columns {', '.join(req.required_columns)}"
            if req.required_keys:
                hint += f" with keys {', '.join(req.required_keys)}"
            errors.append(f"missing required artifact: {path} ({hint})")
            continue
        if req.kind == "csv":
            try:
                df = pd.read_csv(path)
            except Exception as exc:
                errors.append(f"failed to read required artifact: {path} ({exc})")
                continue
            if req.required_columns:
                missing = [col for col in req.required_columns if col not in df.columns]
                if missing:
                    errors.append(
                        f"required artifact missing columns: {path} (missing {', '.join(missing)})"
                    )
        elif req.kind == "json":
            try:
                payload = json.loads(path.read_text())
            except Exception as exc:
                errors.append(f"failed to read required artifact: {path} ({exc})")
                continue
            if req.required_keys:
                missing = [key for key in req.required_keys if key not in payload]
                if missing:
                    errors.append(
                        f"required artifact missing keys: {path} (missing {', '.join(missing)})"
                    )
        else:
            try:
                path.read_bytes()
            except Exception as exc:
                errors.append(f"failed to read required artifact: {path} ({exc})")
    return errors


# ---------- Metric extractors ----------


def tri_engine_metrics(path: Path) -> Dict[str, Any]:
    df, err = _safe_load_csv(path)
    if df is None:
        return _status_block("missing" if err == "file not found" else "parse_error", path, reason=err)

    required = set(_required_artifact("tri_engine_agreement").required_columns)
    if not required.issubset(df.columns):
        missing = ",".join(sorted(required - set(df.columns)))
        return _status_block("parse_error", path, reason=f"missing columns: {missing}")

    mc_error = np.abs(df["mc_price"] - df["bs_price"])
    pde_error = np.abs(df["pde_price"] - df["bs_price"])
    metrics: Dict[str, Any] = {
        "rows": int(len(df)),
        "max_abs_error_mc": float(mc_error.max()),
        "max_abs_error_pde": float(pde_error.max()),
    }

    if "mc_std_error" in df.columns:
        ci_low = df["mc_price"] - 1.96 * df["mc_std_error"]
        ci_high = df["mc_price"] + 1.96 * df["mc_std_error"]
        coverage = ((df["bs_price"] >= ci_low) & (df["bs_price"] <= ci_high)).mean()
        metrics["mc_ci_coverage_fraction"] = float(coverage)
        metrics["mc_ci_covers_bs"] = bool(np.isclose(coverage, 1.0))
    else:
        metrics["mc_ci_covers_bs"] = None
        metrics["mc_ci_coverage_fraction"] = None

    return _status_block("ok", path, metrics=metrics)


def qmc_vs_prng_metrics(path: Path) -> Dict[str, Any]:
    df, err = _safe_load_csv(path)
    if df is None:
        return _status_block("missing" if err == "file not found" else "parse_error", path, reason=err)

    required = set(_required_artifact("qmc_vs_prng_equal_time").required_columns)
    if not required.issubset(df.columns):
        missing = ",".join(sorted(required - set(df.columns)))
        return _status_block("parse_error", path, reason=f"missing columns: {missing}")

    payoffs: Dict[str, Any] = {}
    for payoff, group in df.groupby("payoff"):
        payoffs[str(payoff)] = {
            "rows": int(len(group)),
            "rmse_ratio_median": float(group["rmse_ratio"].median()),
            "rmse_ratio_min": float(group["rmse_ratio"].min()),
            "rmse_ratio_max": float(group["rmse_ratio"].max()),
        }

    metrics = {
        "rmse_ratio_overall_median": float(df["rmse_ratio"].median()),
        "payoffs": payoffs,
    }
    return _status_block("ok", path, metrics=metrics)


def pde_order_metrics(path: Path) -> Dict[str, Any]:
    df, err = _safe_load_csv(path)
    if df is None:
        return _status_block("missing" if err == "file not found" else "parse_error", path, reason=err)

    required = set(_required_artifact("pde_order_slope").required_columns)
    if not required.issubset(df.columns):
        missing = ",".join(sorted(required - set(df.columns)))
        return _status_block("parse_error", path, reason=f"missing columns: {missing}")

    df = df[df["abs_error"] > 0]
    if df.empty:
        return _status_block("parse_error", path, reason="no positive abs_error rows")

    log_nodes = np.log(df["nodes"].to_numpy(dtype=float))
    log_err = np.log(df["abs_error"].to_numpy(dtype=float))
    slope, r2 = _regression_slope(log_nodes, log_err)

    finest_idx = df["nodes"].idxmax()
    finest_row = df.loc[finest_idx]
    metrics = {
        "rows": int(len(df)),
        "slope": float(slope),
        "r2": float(r2),
        "rmse_finest": float(finest_row["abs_error"]),
        "nodes_finest": int(finest_row["nodes"]),
    }
    if "timesteps" in df.columns:
        metrics["timesteps_finest"] = int(finest_row["timesteps"])

    return _status_block("ok", path, metrics=metrics)


def ql_parity_metrics(path: Path) -> Dict[str, Any]:
    df, err = _safe_load_csv(path)
    if df is None:
        return _status_block("missing" if err == "file not found" else "parse_error", path, reason=err)

    required = set(_required_artifact("ql_parity").required_columns)
    if not required.issubset(df.columns):
        missing = ",".join(sorted(required - set(df.columns)))
        return _status_block("parse_error", path, reason=f"missing columns: {missing}")

    by_cat = {}
    for cat, group in df.groupby("category"):
        by_cat[str(cat)] = {
            "max_abs_diff_cents": float(group["abs_diff_cents"].max()),
            "rows": int(len(group)),
        }

    metrics: Dict[str, Any] = {
        "max_abs_diff_cents_overall": float(df["abs_diff_cents"].max()),
        "by_category": by_cat,
    }
    if "runtime_ratio" in df.columns:
        metrics["runtime_ratio_median"] = float(df["runtime_ratio"].median())
        metrics["runtime_ratio_by_category"] = {
            str(cat): float(group["runtime_ratio"].median()) for cat, group in df.groupby("category")
        }

    return _status_block("ok", path, metrics=metrics)


def _collapse_status(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if any(s == "parse_error" for s in statuses):
        return "parse_error"
    if any(s == "missing" for s in statuses):
        return "missing"
    return "ok"


def benchmark_metrics(root: Path) -> Dict[str, Any]:
    mc_paths_path = _required_path("bench_mc_paths", root)
    mc_equal_time_path = _required_path("bench_mc_equal_time", root)

    mc_block: Dict[str, Any] | None = None
    df_mc, err_mc = _safe_load_csv(mc_paths_path)
    if df_mc is None:
        mc_block = _status_block("missing" if err_mc == "file not found" else "parse_error", mc_paths_path, reason=err_mc)
    else:
        try:
            base = df_mc.loc[df_mc["threads"] == 1].iloc[0]
            max_threads_row = df_mc.loc[df_mc["threads"].idxmax()]
            mc_block = _status_block(
                "ok",
                mc_paths_path,
                metrics={
                    "paths_per_sec_1t": float(base["paths_per_sec"]),
                    "paths_per_sec_max_threads": float(max_threads_row["paths_per_sec"]),
                    "threads_max": int(max_threads_row["threads"]),
                    "speedup_max_threads": float(max_threads_row.get("speedup", np.nan)),
                    "efficiency_max_threads": float(max_threads_row.get("efficiency", np.nan)),
                },
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            mc_block = _status_block("parse_error", mc_paths_path, reason=str(exc))

    equal_time_block: Dict[str, Any] | None = None
    df_eq, err_eq = _safe_load_csv(mc_equal_time_path)
    if df_eq is None:
        equal_time_block = _status_block("missing" if err_eq == "file not found" else "parse_error", mc_equal_time_path, reason=err_eq)
    else:
        payoffs: Dict[str, Any] = {}
        try:
            for payoff, group in df_eq.groupby("payoff"):
                prng = group.loc[group["method"].str.upper() == "PRNG", "time_scaled_error"]
                qmc = group.loc[group["method"].str.upper() == "QMC", "time_scaled_error"]
                ratio = None
                if not prng.empty and not qmc.empty:
                    ratio = float(prng.mean() / qmc.mean())
                payoffs[str(payoff)] = {
                    "rows": int(len(group)),
                    "time_scaled_error_ratio_prng_over_qmc": ratio,
                }
            equal_time_block = _status_block(
                "ok",
                mc_equal_time_path,
                metrics={"payoffs": payoffs},
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            equal_time_block = _status_block("parse_error", mc_equal_time_path, reason=str(exc))

    blocks = {"mc_paths": mc_block, "mc_equal_time": equal_time_block}
    overall_status = _collapse_status(b.get("status", "missing") for b in blocks.values())
    return {
        "status": overall_status,
        "sources": {
            "mc_paths": _rel_path(mc_paths_path),
            "mc_equal_time": _rel_path(mc_equal_time_path),
        },
        **blocks,
    }


def _wrds_bundle_label(pricing_df: pd.DataFrame | None) -> str:
    if pricing_df is None:
        return "sample bundle regression harness"
    if "source_today" not in pricing_df.columns or "source_next" not in pricing_df.columns:
        return "sample bundle regression harness"
    sources = set(
        str(val)
        for val in pd.concat([pricing_df["source_today"], pricing_df["source_next"]])
        .dropna()
        .unique()
    )
    if not sources:
        return "sample bundle regression harness"
    if sources == {"sample"}:
        return "sample bundle regression harness"
    if sources == {"local"}:
        return "local WRDS stash"
    if sources == {"wrds"}:
        return "live WRDS"
    if sources == {"cache"}:
        return "WRDS cache"
    if "sample" in sources:
        return f"mixed (sample + {', '.join(sorted(sources - {'sample'}))})"
    return f"mixed ({', '.join(sorted(sources))})"


def wrds_metrics(root: Path) -> Dict[str, Any]:
    pricing_path = _required_path("wrds_agg_pricing", root)
    oos_path = _required_path("wrds_agg_oos", root)
    pnl_path = _required_path("wrds_agg_pnl", root)

    blocks: Dict[str, Any] = {}
    statuses: List[str] = []

    pricing_df, pricing_err = _safe_load_csv(pricing_path)
    if pricing_df is None:
        blocks["bundle"] = "sample bundle regression harness"
        blocks["pricing"] = _status_block("missing" if pricing_err == "file not found" else "parse_error", pricing_path, reason=pricing_err)
        statuses.append(blocks["pricing"]["status"])
    else:
        blocks["bundle"] = _wrds_bundle_label(pricing_df)
        metrics = {
            "rows": int(len(pricing_df)),
            "median_iv_rmse_volpts_vega_wt": float(pricing_df["iv_rmse_volpts_vega_wt"].median()),
            "median_iv_mae_volpts_vega_wt": float(pricing_df["iv_mae_volpts_vega_wt"].median()),
            "median_price_rmse_ticks": float(pricing_df["price_rmse_ticks"].median()),
            "median_iv_mae_bps": float(pricing_df["iv_mae_bps"].median()),
            "median_price_mae_ticks": float(pricing_df["price_mae_ticks"].median()),
        }
        blocks["pricing"] = _status_block("ok", pricing_path, metrics=metrics)
        statuses.append("ok")

    oos_df, oos_err = _safe_load_csv(oos_path)
    if oos_df is None:
        blocks["oos"] = _status_block("missing" if oos_err == "file not found" else "parse_error", oos_path, reason=oos_err)
        statuses.append(blocks["oos"]["status"])
    else:
        weights = oos_df["weight"] if "weight" in oos_df.columns else None
        metrics = {
            "rows": int(len(oos_df)),
            "weighted_iv_mae_bps": _weighted_average(oos_df["iv_mae_bps"], weights),
            "weighted_price_mae_ticks": _weighted_average(oos_df["price_mae_ticks"], weights),
        }
        blocks["oos"] = _status_block("ok", oos_path, metrics=metrics)
        statuses.append("ok")

    pnl_df, pnl_err = _safe_load_csv(pnl_path)
    if pnl_df is None:
        blocks["pnl"] = _status_block("missing" if pnl_err == "file not found" else "parse_error", pnl_path, reason=pnl_err)
        statuses.append(blocks["pnl"]["status"])
    else:
        metrics = {
            "rows": int(len(pnl_df)),
            "mean_pnl_ticks": float(pnl_df["mean_ticks"].mean()),
            "mean_pnl": float(pnl_df["mean_pnl"].mean()),
            "median_pnl_sigma": float(pnl_df["pnl_sigma"].median()),
        }
        blocks["pnl"] = _status_block("ok", pnl_path, metrics=metrics)
        statuses.append("ok")

    overall = _collapse_status(statuses) if statuses else "missing"
    blocks["status"] = overall
    return blocks


# ---------- Markdown rendering ----------


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _highlights(name: str, block: Dict[str, Any]) -> str:
    if block.get("status") != "ok":
        return block.get("reason", "not available")

    metrics = block.get("metrics", {})
    if name == "tri_engine_agreement":
        return (
            f"max|MC-BS|={_fmt(metrics.get('max_abs_error_mc'))}, "
            f"max|PDE-BS|={_fmt(metrics.get('max_abs_error_pde'))}, "
            f"MC CI covers BS={metrics.get('mc_ci_covers_bs')}"
        )
    if name == "qmc_vs_prng_equal_time":
        overall = metrics.get("rmse_ratio_overall_median")
        payoffs = metrics.get("payoffs", {})
        payoff_bits = [
            f"{p}: med={_fmt(info.get('rmse_ratio_median'))}"
            for p, info in payoffs.items()
        ]
        payoff_str = "; ".join(payoff_bits)
        return f"median PRNG/QMC RMSE ratio={_fmt(overall)} ({payoff_str})"
    if name == "pde_order":
        return (
            f"slope={_fmt(metrics.get('slope'))}, "
            f"rmse_finest={_fmt(metrics.get('rmse_finest'))}"
        )
    if name == "ql_parity":
        return f"max diff={_fmt(metrics.get('max_abs_diff_cents_overall'))} cents"
    if name == "benchmarks":
        mc_block = block.get("mc_paths", {})
        mc_metrics = mc_block.get("metrics", {}) if isinstance(mc_block, dict) else {}
        return (
            f"MC paths/sec (1t)={_fmt(mc_metrics.get('paths_per_sec_1t'))}, "
            f"eff@max={_fmt(mc_metrics.get('efficiency_max_threads'))}"
        )
    if name == "wrds":
        pricing = block.get("pricing", {}).get("metrics", {}) if isinstance(block.get("pricing"), dict) else {}
        bundle = block.get("bundle", "bundle")
        return f"median iv_rmse={_fmt(pricing.get('median_iv_rmse_volpts_vega_wt'))} ({bundle})"
    return "ok"


def render_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Metrics Snapshot", ""]
    lines.append(f"Generated at: {summary['generated_at']}")
    lines.append(f"Artifacts root: {summary['artifacts_root']}")
    if summary.get("manifest_git_sha"):
        lines.append(f"Manifest git sha: {summary['manifest_git_sha']}")
    lines.append("")

    lines.append("## Status overview")
    lines.append("| Block | Status | Highlights |")
    lines.append("| --- | --- | --- |")
    for key, block in summary["metrics"].items():
        label = key.replace("_", " ")
        lines.append(f"| {label} | {block.get('status')} | {_highlights(key, block)} |")
    lines.append("")

    for key, block in summary["metrics"].items():
        lines.append(f"### {key.replace('_', ' ').title()}")
        lines.append(f"Status: {block.get('status')}")
        if block.get("reason"):
            lines.append(f"Reason: {block['reason']}")
        metrics = block.get("metrics")
        if metrics:
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("| --- | --- |")
            for m_key, value in metrics.items():
                if isinstance(value, dict):
                    nested = ", ".join(f"{k}={_fmt(v)}" for k, v in value.items())
                    lines.append(f"| {m_key} | {nested} |")
                else:
                    lines.append(f"| {m_key} | {_fmt(value)} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------- CLI ----------


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate artifact-derived metrics snapshot")
    ap.add_argument("--artifacts", type=Path, default=ARTIFACTS_ROOT)
    ap.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--skip-manifest", action="store_true", help="Do not update manifest.json")
    return ap.parse_args()


def build_summary(artifacts_root: Path, manifest_path: Path) -> Dict[str, Any]:
    manifest_info = load_manifest() if manifest_path.exists() else {}
    git_sha = None
    try:
        git_sha = manifest_info.get("git", {}).get("sha")
    except Exception:
        git_sha = None

    tri_engine_path = _required_path("tri_engine_agreement", artifacts_root)
    qmc_path = _required_path("qmc_vs_prng_equal_time", artifacts_root)
    pde_path = _required_path("pde_order_slope", artifacts_root)
    ql_parity_path = _required_path("ql_parity", artifacts_root)

    metrics = {
        "tri_engine_agreement": tri_engine_metrics(tri_engine_path),
        "qmc_vs_prng_equal_time": qmc_vs_prng_metrics(qmc_path),
        "pde_order": pde_order_metrics(pde_path),
        "ql_parity": ql_parity_metrics(ql_parity_path),
        "benchmarks": benchmark_metrics(artifacts_root),
        "wrds": wrds_metrics(artifacts_root),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_root": _rel_path(artifacts_root),
        "manifest_path": _rel_path(manifest_path),
        "manifest_git_sha": git_sha,
        "metrics": metrics,
    }


def main() -> None:
    args = parse_args()
    artifacts_root = args.artifacts.resolve()
    manifest_path = args.manifest.resolve()
    json_out = (args.output_json or artifacts_root / "metrics_summary.json").resolve()
    md_out = (args.output_md or artifacts_root / "metrics_summary.md").resolve()

    summary = build_summary(artifacts_root, manifest_path)

    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    md_out.write_text(render_markdown(summary))

    if not args.skip_manifest:
        inputs: List[str | Path] = [artifacts_root / item.relative_path for item in REQUIRED_ARTIFACTS]
        update_run(
            "metrics_snapshot",
            {
                "generated_at": summary["generated_at"],
                "artifacts_root": str(artifacts_root),
                "output_json": str(json_out),
                "output_md": str(md_out),
                "statuses": {k: v.get("status") for k, v in summary["metrics"].items()},
                "inputs": describe_inputs(inputs),
            },
        )

    errors = _validate_required_artifacts(artifacts_root)
    if errors:
        for err in errors:
            print(f"[metrics_summary] ERROR: {err}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")


if __name__ == "__main__":
    main()

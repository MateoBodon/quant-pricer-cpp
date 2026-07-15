#!/usr/bin/env python3
"""Export license-safe WRDS metrics from aggregated CSV artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_ROOT = REPO_ROOT / "docs" / "artifacts"
LOCAL_ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "_local"
LOCAL_WRDS_ROOT = LOCAL_ARTIFACTS_ROOT / "wrds_local"
SCHEMA_VERSION = "wrds_realdata_metrics_export_v1"


@dataclass
class CsvData:
    path: Path
    rows: List[Dict[str, str]]
    columns: List[str]


def _resolve_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    return path


def _read_csv(path: Path) -> CsvData:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(row) for row in reader]
    return CsvData(path=path, rows=rows, columns=list(reader.fieldnames or []))


RESTRICTED_COLUMN_TOKENS = {
    "ask",
    "best_ask",
    "best_bid",
    "best_offer",
    "bid",
    "cusip",
    "exchange",
    "issue_id",
    "market_iv",
    "mid",
    "open",
    "option_id",
    "optionid",
    "permco",
    "permno",
    "secid",
    "security_id",
    "spot",
    "strike",
    "strike_price",
    "ticker",
    "underlying",
    "volume",
}


ALLOWED_COLUMNS = {
    "wrds_agg_pricing.csv": {
        "trade_date",
        "next_trade_date",
        "label",
        "regime",
        "comment",
        "status",
        "source_today",
        "source_next",
        "iv_rmse_volpts_vega_wt",
        "iv_mae_volpts_vega_wt",
        "iv_p90_bps",
        "price_rmse_ticks",
        "iv_mae_bps",
        "price_mae_ticks",
    },
    "wrds_agg_oos.csv": {
        "tenor_bucket",
        "iv_mae_bps",
        "price_mae_ticks",
        "quotes",
        "weight",
        "trade_date",
        "label",
        "regime",
    },
    "wrds_agg_pnl.csv": {
        "tenor_bucket",
        "mean_pnl",
        "mean_ticks",
        "pnl_sigma",
        "count",
        "trade_date",
        "label",
        "regime",
    },
    "wrds_bs_heston_comparison.csv": {
        "tenor_bucket",
        "heston_iv_rmse_volpts",
        "heston_price_rmse_ticks",
        "bs_iv_rmse_volpts",
        "bs_price_rmse_ticks",
        "heston_oos_iv_mae_bps",
        "heston_oos_price_mae_ticks",
        "bs_oos_iv_mae_bps",
        "bs_oos_price_mae_ticks",
        "heston_pnl_sigma",
        "count",
        "mean_ticks",
        "delta_iv_rmse_volpts",
        "delta_price_rmse_ticks",
        "delta_oos_iv_mae_bps",
        "delta_oos_price_mae_ticks",
    },
}


def _validate_columns(data: CsvData, filename: str) -> None:
    columns = data.columns
    if not columns:
        raise ValueError(f"{filename} is missing header columns")
    allowed = ALLOWED_COLUMNS.get(filename)
    if allowed is None:
        raise ValueError(f"{filename} is not an approved WRDS aggregate")
    unknown = sorted(set(columns) - allowed)
    if unknown:
        raise ValueError(f"{filename} has unexpected columns: {', '.join(unknown)}")
    restricted_hits = [
        col
        for col in columns
        if any(token in col.lower() for token in RESTRICTED_COLUMN_TOKENS)
    ]
    if restricted_hits:
        raise ValueError(
            f"{filename} includes restricted columns: {', '.join(restricted_hits)}"
        )


def _coerce_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    lower = raw.lower()
    if lower in {"nan", "na", "none", "null"}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _column_values(rows: Iterable[Dict[str, str]], key: str) -> List[float]:
    values: List[float] = []
    for row in rows:
        val = _coerce_float(row.get(key))
        if val is not None:
            values.append(val)
    return values


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / float(len(values))


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def _weighted_average_from_rows(
    rows: Iterable[Dict[str, str]],
    value_key: str,
    weight_keys: Iterable[str],
) -> Optional[float]:
    total = 0.0
    total_weight = 0.0
    fallback_values: List[float] = []
    for row in rows:
        value = _coerce_float(row.get(value_key))
        if value is None:
            continue
        weight = None
        for key in weight_keys:
            weight = _coerce_float(row.get(key))
            if weight is not None:
                break
        if weight is None:
            fallback_values.append(value)
            continue
        total += value * weight
        total_weight += weight
    if total_weight > 0:
        return total / total_weight
    return _mean(fallback_values)


def _date_range(rows: Iterable[Dict[str, str]], key: str) -> Optional[Dict[str, str]]:
    dates = [row.get(key) for row in rows if row.get(key)]
    if not dates:
        return None
    return {"start": min(dates), "end": max(dates)}


def _load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _normalize_manifest_path(path: str | Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = (REPO_ROOT / value).resolve()
    else:
        value = value.resolve()
    return value


def _find_wrds_run(
    manifest: Dict[str, Any], wrds_root: Path
) -> Optional[Dict[str, Any]]:
    runs = manifest.get("runs", {}).get("wrds_dateset", [])
    if not isinstance(runs, list) or not runs:
        return None
    target = (wrds_root / "wrds_agg_pricing.csv").resolve()
    for entry in reversed(runs):
        pricing = entry.get("pricing_csv")
        if not pricing:
            continue
        if _normalize_manifest_path(pricing) == target:
            return entry
    return runs[-1]


def _git_sha() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return None


def _machine_label(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    env_label = os.environ.get("QUANT_MACHINE_LABEL")
    if env_label:
        return env_label
    node = platform.node().strip()
    return node or "unknown"


def _infer_data_mode(use_sample: bool) -> str:
    if use_sample or os.environ.get("WRDS_USE_SAMPLE") == "1":
        return "sample"
    if os.environ.get("WRDS_LOCAL_ROOT"):
        return "local"
    return "live"


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def build_metrics(
    pricing: CsvData, oos: CsvData, pnl: CsvData, comparison: CsvData
) -> Dict[str, Any]:
    pricing_rows = pricing.rows
    oos_rows = oos.rows
    pnl_rows = pnl.rows
    comp_rows = comparison.rows

    pricing_metrics = {
        "rows": len(pricing_rows),
        "median_iv_rmse_volpts_vega_wt": _median(
            _column_values(pricing_rows, "iv_rmse_volpts_vega_wt")
        ),
        "median_iv_mae_volpts_vega_wt": _median(
            _column_values(pricing_rows, "iv_mae_volpts_vega_wt")
        ),
        "median_iv_p90_bps": _median(_column_values(pricing_rows, "iv_p90_bps")),
        "median_price_rmse_ticks": _median(
            _column_values(pricing_rows, "price_rmse_ticks")
        ),
        "median_iv_mae_bps": _median(_column_values(pricing_rows, "iv_mae_bps")),
        "median_price_mae_ticks": _median(
            _column_values(pricing_rows, "price_mae_ticks")
        ),
    }

    oos_metrics = {
        "rows": len(oos_rows),
        "weighted_iv_mae_bps": _weighted_average_from_rows(
            oos_rows, "iv_mae_bps", ["weight", "quotes"]
        ),
        "weighted_price_mae_ticks": _weighted_average_from_rows(
            oos_rows, "price_mae_ticks", ["weight", "quotes"]
        ),
    }

    pnl_metrics = {
        "rows": len(pnl_rows),
        "mean_pnl_ticks": _mean(_column_values(pnl_rows, "mean_ticks")),
        "mean_pnl": _mean(_column_values(pnl_rows, "mean_pnl")),
        "median_pnl_sigma": _median(_column_values(pnl_rows, "pnl_sigma")),
    }

    comparison_metrics = {
        "rows": len(comp_rows),
        "median_heston_iv_rmse_volpts": _median(
            _column_values(comp_rows, "heston_iv_rmse_volpts")
        ),
        "median_bs_iv_rmse_volpts": _median(
            _column_values(comp_rows, "bs_iv_rmse_volpts")
        ),
        "median_delta_iv_rmse_volpts": _median(
            _column_values(comp_rows, "delta_iv_rmse_volpts")
        ),
        "median_heston_price_rmse_ticks": _median(
            _column_values(comp_rows, "heston_price_rmse_ticks")
        ),
        "median_bs_price_rmse_ticks": _median(
            _column_values(comp_rows, "bs_price_rmse_ticks")
        ),
        "median_delta_price_rmse_ticks": _median(
            _column_values(comp_rows, "delta_price_rmse_ticks")
        ),
        "median_heston_oos_iv_mae_bps": _median(
            _column_values(comp_rows, "heston_oos_iv_mae_bps")
        ),
        "median_bs_oos_iv_mae_bps": _median(
            _column_values(comp_rows, "bs_oos_iv_mae_bps")
        ),
        "median_delta_oos_iv_mae_bps": _median(
            _column_values(comp_rows, "delta_oos_iv_mae_bps")
        ),
        "median_heston_pnl_sigma": _median(
            _column_values(comp_rows, "heston_pnl_sigma")
        ),
    }

    return {
        "pricing": pricing_metrics,
        "oos": oos_metrics,
        "pnl": pnl_metrics,
        "comparison": comparison_metrics,
    }


def _rel_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def render_markdown(payload: Dict[str, Any]) -> str:
    provenance = payload["provenance"]
    metrics = payload["metrics"]
    lines = [
        "# WRDS real-data metrics export",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Provenance",
        f"- panel_id: {provenance.get('panel_id')}",
        f"- trade_date_range: {_fmt(provenance.get('trade_date_range'))}",
        f"- next_trade_date_range: {_fmt(provenance.get('next_trade_date_range'))}",
        f"- data_mode: {provenance.get('data_mode')}",
        f"- git_sha: {provenance.get('git_sha')}",
        f"- machine_label: {provenance.get('machine_label')}",
        "",
        "## Metrics",
    ]

    for section in ["pricing", "oos", "pnl", "comparison"]:
        block = metrics.get(section, {})
        lines.append(f"### {section}")
        lines.append("| metric | value |")
        lines.append("| --- | --- |")
        for key, value in block.items():
            lines.append(f"| {key} | {_fmt(value)} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Export license-safe WRDS metrics from aggregated CSV artifacts."
    )
    ap.add_argument(
        "--wrds-root",
        default=None,
        help=(
            "Directory containing WRDS aggregated artifacts "
            "(default: docs/artifacts/wrds for sample, artifacts/_local/wrds_local for local)."
        ),
    )
    ap.add_argument(
        "--use-sample", action="store_true", help="Force sample-mode provenance."
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help=(
            "Manifest path for provenance "
            "(default: docs/artifacts/manifest.json for sample or <wrds_root>/manifest_local.json for local)."
        ),
    )
    ap.add_argument("--panel-id", default=None, help="Override panel_id provenance.")
    ap.add_argument("--git-sha", default=None, help="Override git SHA provenance.")
    ap.add_argument("--data-mode", default=None, help="Override data_mode provenance.")
    ap.add_argument(
        "--machine-label",
        default=None,
        help="Override machine label provenance (or set QUANT_MACHINE_LABEL).",
    )
    ap.add_argument(
        "--out",
        default=None,
        help=(
            "Output JSON path "
            "(default: artifacts/_local/wrds_local/metrics_export.json)."
        ),
    )
    ap.add_argument(
        "--out-md",
        default=None,
        help=(
            "Output Markdown path "
            "(default: artifacts/_local/wrds_local/metrics_export.md)."
        ),
    )
    args = ap.parse_args()

    env_use_sample = os.environ.get("WRDS_USE_SAMPLE") == "1"
    use_sample = args.use_sample or env_use_sample

    if args.wrds_root:
        wrds_root = _resolve_path(args.wrds_root)
    else:
        if use_sample:
            wrds_root = ARTIFACTS_ROOT / "wrds"
        else:
            wrds_root = LOCAL_WRDS_ROOT

    manifest_override = args.manifest or os.environ.get("QUANT_MANIFEST_PATH")
    if manifest_override:
        manifest_path = _resolve_path(manifest_override)
    elif use_sample:
        manifest_path = ARTIFACTS_ROOT / "manifest.json"
    else:
        manifest_path = wrds_root / "manifest_local.json"

    pricing = _read_csv(wrds_root / "wrds_agg_pricing.csv")
    oos = _read_csv(wrds_root / "wrds_agg_oos.csv")
    pnl = _read_csv(wrds_root / "wrds_agg_pnl.csv")
    comparison = _read_csv(wrds_root / "wrds_bs_heston_comparison.csv")

    _validate_columns(pricing, "wrds_agg_pricing.csv")
    _validate_columns(oos, "wrds_agg_oos.csv")
    _validate_columns(pnl, "wrds_agg_pnl.csv")
    _validate_columns(comparison, "wrds_bs_heston_comparison.csv")

    manifest = _load_manifest(manifest_path)
    wrds_run = _find_wrds_run(manifest, wrds_root)

    panel_id = args.panel_id or (wrds_run or {}).get("panel_id") or "unknown"
    trade_date_range = (wrds_run or {}).get("trade_date_range") or _date_range(
        pricing.rows, "trade_date"
    )
    next_trade_date_range = (wrds_run or {}).get(
        "next_trade_date_range"
    ) or _date_range(pricing.rows, "next_trade_date")
    git_sha = (
        args.git_sha
        or (manifest.get("git", {}) if manifest else {}).get("sha")
        or _git_sha()
    )
    if args.data_mode:
        data_mode = args.data_mode
    elif use_sample:
        data_mode = "sample"
    else:
        data_mode = (wrds_run or {}).get("data_mode") or _infer_data_mode(False)
    machine_label = _machine_label(args.machine_label)

    metrics = build_metrics(pricing, oos, pnl, comparison)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "panel_id": panel_id,
            "trade_date_range": trade_date_range,
            "next_trade_date_range": next_trade_date_range,
            "data_mode": data_mode,
            "git_sha": git_sha,
            "machine_label": machine_label,
        },
        "inputs": {
            "wrds_root": _rel_or_abs(wrds_root),
            "pricing_csv": _rel_or_abs(pricing.path),
            "oos_csv": _rel_or_abs(oos.path),
            "pnl_csv": _rel_or_abs(pnl.path),
            "comparison_csv": _rel_or_abs(comparison.path),
            "manifest": _rel_or_abs(manifest_path),
        },
        "metrics": metrics,
    }

    out_path = _resolve_path(args.out or (LOCAL_WRDS_ROOT / "metrics_export.json"))
    out_md = _resolve_path(args.out_md or (LOCAL_WRDS_ROOT / "metrics_export.md"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    out_md.write_text(render_markdown(payload))

    print(f"[wrds_export] wrote {out_path}")
    print(f"[wrds_export] wrote {out_md}")


if __name__ == "__main__":
    main()

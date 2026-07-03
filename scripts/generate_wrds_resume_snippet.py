#!/usr/bin/env python3
"""Generate a resume-ready markdown snippet from WRDS metrics export JSON."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

BANNED_TOKEN_PATTERNS = [
    r"/srv/data/wrds",
    r"\.parquet",
    r"\.csv",
]

ROW_LEVEL_PATTERNS = [
    r"(?m)^([^,\n]*,){4,}[^,\n]*$",  # csv-like row dumps
    r"(?m)^\s*\{\s*\"",  # raw JSON object dumps
    r"(?m)^\s*\[\s*\{",  # raw JSON array dumps
]


def _resolve_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    else:
        path = path.resolve()
    return path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"metrics JSON not found: {path}")
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("metrics export payload must be a JSON object")
    return payload


def _require_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing/invalid '{key}' object in metrics export")
    return value


def _require_text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if value is None:
        raise ValueError(f"missing required field: {key}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"empty required field: {key}")
    return text


def _as_float(parent: dict[str, Any], key: str) -> float:
    value = parent.get(key)
    if value is None:
        raise ValueError(f"missing required metric: {key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"metric '{key}' is not numeric: {value!r}") from exc


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}"


def _infer_mode(metrics_path: Path, provenance: dict[str, Any]) -> str:
    name = metrics_path.name.lower()
    if "metrics_export_sample" in name:
        return "sample"
    if "metrics_export_local" in name:
        return "local"
    data_mode = str(provenance.get("data_mode", "")).strip().lower()
    if data_mode == "sample":
        return "sample"
    return "local"


def _output_path(metrics_path: Path, mode: str, output: str | None) -> Path:
    if output:
        return _resolve_path(output)
    return (metrics_path.parent / f"resume_snippet_wrds_{mode}.md").resolve()


def _build_snippet(payload: dict[str, Any], mode: str, metrics_filename: str) -> str:
    schema_version = str(payload.get("schema_version", "")).strip()
    if not schema_version.startswith("wrds_realdata_metrics_export_v"):
        raise ValueError("unsupported schema_version for resume snippet generator")

    generated_at = _require_text(payload, "generated_at")

    provenance = _require_dict(payload, "provenance")
    trade_range = _require_dict(provenance, "trade_date_range")
    next_trade_range = _require_dict(provenance, "next_trade_date_range")

    panel_id = _require_text(provenance, "panel_id")
    machine_label = _require_text(provenance, "machine_label")
    git_sha = _require_text(provenance, "git_sha")
    trade_start = _require_text(trade_range, "start")
    trade_end = _require_text(trade_range, "end")
    next_start = _require_text(next_trade_range, "start")
    next_end = _require_text(next_trade_range, "end")

    metrics = _require_dict(payload, "metrics")
    pricing = _require_dict(metrics, "pricing")
    comparison = _require_dict(metrics, "comparison")

    pricing_iv_rmse = _as_float(pricing, "median_iv_rmse_volpts_vega_wt")
    pricing_iv_mae_bps = _as_float(pricing, "median_iv_mae_bps")
    heston_iv_rmse = _as_float(comparison, "median_heston_iv_rmse_volpts")
    bs_iv_rmse = _as_float(comparison, "median_bs_iv_rmse_volpts")
    delta_iv_rmse = _as_float(comparison, "median_delta_iv_rmse_volpts")
    if bs_iv_rmse <= 0:
        raise ValueError("metric 'median_bs_iv_rmse_volpts' must be > 0 to compute percent improvement")
    improvement_pct = ((bs_iv_rmse - heston_iv_rmse) / bs_iv_rmse) * 100.0
    improvement_direction = "lower" if improvement_pct >= 0 else "higher"
    improvement_pct_abs = abs(improvement_pct)

    bullets = [
        (
            "- WRDS "
            f"{mode} panel `{panel_id}` over {trade_start} to {trade_end} "
            f"(next-trade {next_start} to {next_end}), machine `{machine_label}`, "
            f"commit `{git_sha[:12]}`."
        ),
        (
            "- Pricing aggregate: median vega-weighted IV RMSE "
            f"`{_fmt(pricing_iv_rmse)}` vol pts and median IV MAE `"
            f"{_fmt(pricing_iv_mae_bps)}` bps."
        ),
        (
            "- Heston vs BS aggregate: median IV RMSE `"
            f"{_fmt(heston_iv_rmse)}` vs `{_fmt(bs_iv_rmse)}` "
            f"(delta `{_fmt(delta_iv_rmse)}`, "
            f"~{_fmt_pct(improvement_pct_abs)}% {improvement_direction})."
        ),
    ]

    lines = [
        f"# WRDS Resume Snippet ({mode})",
        f"Source: `{metrics_filename}`",
        f"Generated at: `{generated_at}`",
        "",
        *bullets,
    ]
    return "\n".join(lines)


def _run_sanitization_guard(content: str) -> None:
    lower = content.lower()
    for pattern in BANNED_TOKEN_PATTERNS:
        if re.search(pattern, lower):
            raise ValueError(f"sanitization guard failed: banned token pattern '{pattern}'")

    for pattern in ROW_LEVEL_PATTERNS:
        if re.search(pattern, content):
            raise ValueError(f"sanitization guard failed: row-level pattern '{pattern}'")

    bullet_count = len([line for line in content.splitlines() if line.startswith("- ")])
    if bullet_count < 1 or bullet_count > 3:
        raise ValueError("sanitization guard failed: snippet must contain 1-3 bullet lines")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-json", required=True, help="Path to metrics_export_{sample,local}.json")
    parser.add_argument("--output", default=None, help="Optional output markdown path")
    args = parser.parse_args()

    metrics_path = _resolve_path(args.metrics_json)
    payload = _read_json(metrics_path)
    provenance = _require_dict(payload, "provenance")
    mode = _infer_mode(metrics_path, provenance)
    output_path = _output_path(metrics_path, mode, args.output)

    snippet = _build_snippet(payload, mode=mode, metrics_filename=metrics_path.name)
    _run_sanitization_guard(snippet)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(snippet + "\n")
    print(_display_path(output_path))


if __name__ == "__main__":
    main()

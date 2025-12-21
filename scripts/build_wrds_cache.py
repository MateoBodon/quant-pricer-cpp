#!/usr/bin/env python3
"""Populate a real-data WRDS cache for deterministic runs.

This script pulls OptionMetrics IvyDB slices for a symbol/date range and stores
parquet files under a cache root (default: /Volumes/Storage/Data/wrds_cache).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import warnings
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wrds_pipeline import ingest_sppx_surface

warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy connectable",
)

DEFAULT_CACHE_ROOT = Path("/Volumes/Storage/Data/wrds_cache")
DEFAULT_START = "2010-01-01"


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _bdates(start: str, end: str) -> List[str]:
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    return [d.date().isoformat() for d in pd.bdate_range(start_dt, end_dt)]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(cache_root: Path, symbol: str, trade_date: str) -> Path:
    d = pd.to_datetime(trade_date).date()
    symbol = symbol.upper()
    return cache_root / "optionm" / symbol / str(d.year) / f"{symbol.lower()}_{d}.parquet"


def _cache_meta_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(".json")


def _write_cache(cache_root: Path, symbol: str, trade_date: str, df: pd.DataFrame) -> dict:
    cache_path = _cache_path(cache_root, symbol, trade_date)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False, compression="zstd")
    meta = {
        "symbol": symbol.upper(),
        "trade_date": str(pd.to_datetime(trade_date).date()),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "wrds",
        "path": str(cache_path),
        "size_bytes": cache_path.stat().st_size,
    }
    _cache_meta_path(cache_path).write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return meta


def _load_dateset(path: Path) -> List[str]:
    text = path.read_text()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to parse YAML datesets") from exc
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise RuntimeError("dateset must be a mapping with 'dates'")
    entries = payload.get("dates", [])
    dates: List[str] = []
    for entry in entries:
        trade = entry.get("trade_date")
        next_trade = entry.get("next_trade_date")
        if trade:
            dates.append(str(trade))
        if next_trade:
            dates.append(str(next_trade))
    return sorted(set(dates))


def _require_wrds_env() -> None:
    if not ingest_sppx_surface._has_wrds_credentials():
        raise SystemExit(
            "WRDS credentials not found. Set WRDS_ENABLED=1 with WRDS_USERNAME/WRDS_PASSWORD."
        )


def _iter_dates(args: argparse.Namespace) -> List[str]:
    if args.dateset:
        return _load_dateset(Path(args.dateset))
    return _bdates(args.start_date, args.end_date)


def _write_manifest(cache_root: Path, summary: dict) -> None:
    manifest_path = cache_root / "cache_manifest.json"
    manifest_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def _append_index(index_path: Path, entry: dict) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _summarize_index(index_path: Path) -> dict:
    latest: dict[str, dict] = {}
    if not index_path.exists():
        return {
            "cached_count": 0,
            "missing_count": 0,
            "error_count": 0,
            "rows_total": 0,
            "bytes_total": 0,
        }
    with index_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            entry = json.loads(line)
            trade_date = entry.get("trade_date")
            if trade_date:
                latest[str(trade_date)] = entry

    cached_dates: List[str] = []
    missing_dates: List[str] = []
    errors: List[str] = []
    rows_total = 0
    bytes_total = 0
    cached_count = 0
    for trade_date, entry in latest.items():
        status = entry.get("status")
        if status in {"cached", "exists"}:
            cached_dates.append(trade_date)
            cached_count += 1
            rows_total += int(entry.get("rows", 0) or 0)
            bytes_total += int(entry.get("size_bytes", 0) or 0)
        elif status == "empty":
            missing_dates.append(trade_date)
        elif status == "error":
            err = entry.get("error", "")
            errors.append(f"{trade_date}: {err}")

    date_range = None
    if cached_dates:
        cached_dates_sorted = sorted(cached_dates)
        date_range = {
            "start": cached_dates_sorted[0],
            "end": cached_dates_sorted[-1],
        }
    return {
        "cached_count": cached_count,
        "missing_count": len(missing_dates),
        "error_count": len(errors),
        "rows_total": rows_total,
        "bytes_total": bytes_total,
        "date_range": date_range,
        "missing_dates": sorted(missing_dates),
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a WRDS parquet cache for OptionMetrics slices.")
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--start-date", default=DEFAULT_START)
    ap.add_argument("--end-date", default=(_today_utc() - timedelta(days=1)).isoformat())
    ap.add_argument("--dateset", default=None, help="Optional YAML/JSON dateset to cache")
    ap.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT))
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--hash", action="store_true", help="Compute sha256 for cached files")
    ap.add_argument("--max-dates", type=int, default=None, help="Optional limit for testing")
    ap.add_argument("--log-every", type=int, default=50, help="Log every N cached dates")
    ap.add_argument("--rebuild-manifest", action="store_true", help="Rebuild cache_manifest.json from index")
    args = ap.parse_args()

    cache_root = Path(args.cache_root).expanduser()
    cache_root.mkdir(parents=True, exist_ok=True)
    symbol = args.symbol.upper()

    index_path = cache_root / "cache_index.jsonl"

    if args.rebuild_manifest:
        summary = _summarize_index(index_path)
        manifest = {
            "symbol": symbol,
            "cache_root": str(cache_root),
            "cache_index": str(index_path),
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Rebuilt from cache_index.jsonl",
        }
        _write_manifest(cache_root, manifest)
        print(f"[wrds-cache] rebuilt manifest at {cache_root / 'cache_manifest.json'}")
        return

    _require_wrds_env()

    dates = _iter_dates(args)
    if args.max_dates:
        dates = dates[: args.max_dates]
    print(
        f"[wrds-cache] start symbol={symbol} dates={len(dates)} range={args.start_date}..{args.end_date}"
    )

    total_rows = 0
    cached = 0
    missing: List[str] = []
    errors: List[str] = []

    for idx, trade_date in enumerate(dates, start=1):
        cache_path = _cache_path(cache_root, symbol, trade_date)
        if cache_path.exists() and not args.overwrite:
            cached += 1
            _append_index(
                index_path,
                {
                    "trade_date": trade_date,
                    "path": str(cache_path),
                    "status": "exists",
                },
            )
            continue
        try:
            df = ingest_sppx_surface._fetch_from_wrds(symbol, trade_date)
        except Exception as exc:
            errors.append(f"{trade_date}: {exc}")
            _append_index(
                index_path,
                {
                    "trade_date": trade_date,
                    "status": "error",
                    "error": str(exc),
                },
            )
            continue
        if df.empty:
            missing.append(trade_date)
            _append_index(
                index_path,
                {
                    "trade_date": trade_date,
                    "status": "empty",
                },
            )
            continue
        meta = _write_cache(cache_root, symbol, trade_date, df)
        if args.hash:
            meta["sha256"] = _sha256(Path(meta["path"]))
            _cache_meta_path(Path(meta["path"])).write_text(
                json.dumps(meta, indent=2, sort_keys=True) + "\n"
            )
        total_rows += int(meta.get("rows", 0))
        cached += 1
        _append_index(
            index_path,
            {
                "trade_date": trade_date,
                "path": meta["path"],
                "rows": meta["rows"],
                "size_bytes": meta["size_bytes"],
                "status": "cached",
            },
        )
        if args.log_every > 0 and (idx % args.log_every == 0 or idx == len(dates)):
            print(f"[wrds-cache] {trade_date}: {meta['rows']} rows -> {meta['path']}")

    summary = {
        "symbol": symbol,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "dates_requested": len(dates),
        "dates_cached": cached,
        "rows_total": total_rows,
        "missing_dates": missing,
        "errors": errors,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cache_root": str(cache_root),
        "cache_index": str(index_path),
        "query": {
            "source": "optionm.opprcdYYYY + optionm.secprdYYYY",
            "filters": {
                "cp_flag": "C",
                "best_bid": ">0",
                "best_offer": ">best_bid",
                "limit": 6000,
            },
            "columns": [
                "date",
                "exdate",
                "cp_flag",
                "strike",
                "best_bid",
                "best_offer",
                "forward_price",
                "spot",
                "rate",
                "divyield",
            ],
        },
        "notes": "Cache contains raw WRDS slices used by the pipeline (pre-filter, calls only).",
    }
    manifest = {
        "symbol": symbol,
        "last_run": summary,
        "summary": _summarize_index(index_path),
        "cache_root": str(cache_root),
        "cache_index": str(index_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": "Cache contains raw WRDS slices used by the pipeline (pre-filter, calls only).",
    }
    _write_manifest(cache_root, manifest)

    print(f"[wrds-cache] done. cached={cached}, missing={len(missing)}, errors={len(errors)}")
    if errors:
        print("[wrds-cache] errors:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()

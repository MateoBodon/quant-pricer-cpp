#!/usr/bin/env python3
"""Fail-closed reader for the shared partitioned OptionMetrics vault.

The adapter intentionally binds every load to one explicit acquisition
snapshot.  It reads only the day/month/table partitions needed for a requested
SPX surface, validates those files against their acquisition manifests, and
returns a provenance receipt without copying restricted rows into the repo.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd

DEFAULT_SNAPSHOT = "20260707_045553_global_project_priority"
RECEIPT_SCHEMA = "quant-pricer-wrds-vault-receipt/v1"
RECEIPT_ATTR = "wrds_vault_receipt"
MIN_PIPELINE_DTE_DAYS = 21
MAX_PIPELINE_DTE_DAYS = 720
READ_CHUNK_ROWS = 100_000

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_COMMON_MANIFEST = Path(
    "_manifests/20260707T141203Z_resume_90m_fast_csvgz/manifest.json"
)


class VaultAdapterError(RuntimeError):
    """Raised when a vault input cannot support an exact real-data result."""


def _validate_component(value: str, label: str) -> str:
    if not value or not _SAFE_COMPONENT.fullmatch(value):
        raise VaultAdapterError(f"Invalid {label}: {value!r}")
    return value


def _normalize_trade_date(value: str) -> str:
    try:
        parsed = pd.Timestamp(value)
    except Exception as exc:
        raise VaultAdapterError(f"Invalid trade date: {value!r}") from exc
    if pd.isna(parsed):
        raise VaultAdapterError(f"Invalid trade date: {value!r}")
    return parsed.date().isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _same_file(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, OSError):
        return left.resolve() == right.resolve()


def _as_int(value: Any, label: str) -> int:
    try:
        converted = int(value)
    except (TypeError, ValueError) as exc:
        raise VaultAdapterError(f"Invalid integer {label}: {value!r}") from exc
    return converted


def _source_paths(
    root: Path, trade_date: str, snapshot: str
) -> Dict[str, Tuple[Path, str]]:
    date = pd.Timestamp(trade_date)
    year = date.year
    month = date.strftime("%Y-%m")
    optionm = root / "raw" / "optionm"
    return {
        "opprcd": (
            optionm
            / f"opprcd{year}"
            / f"snapshot={snapshot}"
            / f"day={trade_date}"
            / "data.csv.gz",
            f"day={trade_date}",
        ),
        "secprd": (
            optionm
            / f"secprd{year}"
            / f"snapshot={snapshot}"
            / f"month={month}"
            / "data.csv.gz",
            f"month={month}",
        ),
        "secnmd": (
            optionm / "secnmd" / f"snapshot={snapshot}" / "data.csv.gz",
            "table",
        ),
        "zerocd": (
            optionm / "zerocd" / f"snapshot={snapshot}" / "data.csv.gz",
            "table",
        ),
        "idxdvd": (
            optionm / "idxdvd" / f"snapshot={snapshot}" / "data.csv.gz",
            "table",
        ),
    }


def is_vault_root(root: Path | str, snapshot: str = DEFAULT_SNAPSHOT) -> bool:
    """Return whether ``root`` exposes the required snapshot metadata tables."""

    root = Path(root).expanduser()
    try:
        _validate_component(snapshot, "snapshot")
    except VaultAdapterError:
        return False
    required = _source_paths(root, "2020-01-01", snapshot)
    return all(required[name][0].exists() for name in ("secnmd", "zerocd", "idxdvd"))


def _manifest_candidates(root: Path, table: str) -> Iterable[Path]:
    manifest_root = root / "_manifests"
    candidates: list[Path] = []
    common = root / _COMMON_MANIFEST
    if table in {"secnmd", "zerocd", "idxdvd"} and common.is_file():
        candidates.append(common)
    for pattern in (f"*optionm_{table}_*/manifest.json", f"*{table}*/manifest.json"):
        candidates.extend(sorted(manifest_root.glob(pattern)))
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            yield candidate


def _load_manifest_binding(root: Path, table: str, source_path: Path) -> Dict[str, Any]:
    matches: list[tuple[Path, Dict[str, Any], Dict[str, Any]]] = []
    for manifest_path in _manifest_candidates(root, table):
        try:
            payload = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise VaultAdapterError(
                f"Unreadable source manifest: {manifest_path}"
            ) from exc
        items = payload.get("items")
        if not isinstance(items, list):
            raise VaultAdapterError(
                f"Source manifest has no items list: {manifest_path}"
            )
        for item in items:
            if not isinstance(item, dict) or item.get("table") != table:
                continue
            raw_path = item.get("path")
            if raw_path and _same_file(Path(str(raw_path)), source_path):
                matches.append((manifest_path, payload, item))

    if not matches:
        raise VaultAdapterError(
            f"No acquisition-manifest item binds {table} to {source_path}"
        )
    if len(matches) != 1:
        manifests = ", ".join(str(match[0]) for match in matches)
        raise VaultAdapterError(
            f"Ambiguous acquisition-manifest binding for {table}: {manifests}"
        )

    manifest_path, payload, item = matches[0]
    if item.get("status") != "ok":
        raise VaultAdapterError(
            f"Acquisition-manifest item for {table} is not ok: {item.get('status')!r}"
        )
    stat = source_path.stat()
    manifest_size = _as_int(item.get("size_bytes"), f"{table}.size_bytes")
    if manifest_size != stat.st_size:
        raise VaultAdapterError(
            f"Size mismatch for {table}: manifest={manifest_size}, file={stat.st_size}"
        )
    rows = _as_int(item.get("rows"), f"{table}.rows")
    return {
        "path": manifest_path,
        "sha256": _sha256(manifest_path),
        "overall_status": payload.get("status"),
        "item_status": item.get("status"),
        "item_rows": rows,
        "item_size_bytes": manifest_size,
    }


def _validate_source(
    root: Path, table: str, path: Path, partition: str
) -> tuple[Dict[str, Any], tuple[int, int]]:
    if not path.is_file():
        raise VaultAdapterError(f"Missing vault partition for {table}: {path}")
    before = path.stat()
    binding = _load_manifest_binding(root, table, path)
    receipt = {
        "table": table,
        "partition": partition,
        "relative_path": str(path.relative_to(root)),
        "absolute_path": str(path.resolve()),
        "bytes": before.st_size,
        "sha256": _sha256(path),
        "source_manifest": {
            "relative_path": str(binding["path"].relative_to(root)),
            "absolute_path": str(binding["path"].resolve()),
            "sha256": binding["sha256"],
            "overall_status": binding["overall_status"],
            "item_status": binding["item_status"],
            "item_rows": binding["item_rows"],
            "item_size_bytes": binding["item_size_bytes"],
        },
    }
    return receipt, (before.st_size, before.st_mtime_ns)


def _assert_source_unchanged(path: Path, before: tuple[int, int], table: str) -> None:
    after = path.stat()
    if (after.st_size, after.st_mtime_ns) != before:
        raise VaultAdapterError(f"Vault partition changed during read: {table}")


def _read_chunks(path: Path, usecols: list[str]) -> Iterable[pd.DataFrame]:
    try:
        return pd.read_csv(
            path,
            usecols=usecols,
            dtype={column: "string" for column in usecols},
            chunksize=READ_CHUNK_ROWS,
            low_memory=False,
        )
    except (OSError, ValueError) as exc:
        raise VaultAdapterError(f"Cannot read required columns from {path}") from exc


def _resolve_secid(
    path: Path, symbol: str, trade_date: str, expected_rows: int
) -> tuple[int, Dict[str, int]]:
    source_rows = 0
    ticker_frames: list[pd.DataFrame] = []
    for chunk in _read_chunks(path, ["secid", "effect_date", "ticker"]):
        source_rows += len(chunk)
        ticker = chunk["ticker"].str.strip().str.upper()
        selected = chunk[ticker == symbol]
        if not selected.empty:
            ticker_frames.append(selected)
    if source_rows != expected_rows:
        raise VaultAdapterError(
            f"secnmd row-count mismatch: manifest={expected_rows}, read={source_rows}"
        )
    if not ticker_frames:
        raise VaultAdapterError(f"No secnmd rows for ticker {symbol}")
    candidates = pd.concat(ticker_frames, ignore_index=True)
    effects = pd.to_datetime(candidates["effect_date"], errors="coerce")
    if effects.isna().any():
        raise VaultAdapterError(f"Invalid secnmd effect_date for ticker {symbol}")
    asof = candidates[effects <= pd.Timestamp(trade_date)].copy()
    if asof.empty:
        raise VaultAdapterError(f"No as-of secnmd row for {symbol} on {trade_date}")
    asof_effects = pd.to_datetime(asof["effect_date"], errors="raise")
    latest_date = asof_effects.max()
    latest = asof[asof_effects == latest_date]
    secids = pd.to_numeric(latest["secid"], errors="coerce")
    if secids.isna().any() or (secids % 1 != 0).any():
        raise VaultAdapterError(f"Invalid as-of secid for {symbol} on {trade_date}")
    unique = sorted({int(value) for value in secids})
    if len(unique) != 1:
        raise VaultAdapterError(
            f"Ambiguous as-of secid for {symbol} on {trade_date}: {len(unique)} candidates"
        )
    return unique[0], {
        "source_rows": source_rows,
        "ticker_rows": len(candidates),
        "asof_rows": len(asof),
        "latest_effect_date_rows": len(latest),
        "resolved_unique_secids": len(unique),
    }


def _read_spot(
    path: Path, secid: int, trade_date: str, expected_rows: int
) -> tuple[float, Dict[str, int]]:
    source_rows = 0
    date_rows = 0
    matches: list[pd.DataFrame] = []
    for chunk in _read_chunks(path, ["secid", "date", "close"]):
        source_rows += len(chunk)
        date_mask = chunk["date"].str.strip() == trade_date
        date_rows += int(date_mask.sum())
        secids = pd.to_numeric(chunk["secid"], errors="coerce")
        selected = chunk[date_mask & (secids == secid)]
        if not selected.empty:
            matches.append(selected)
    if source_rows != expected_rows:
        raise VaultAdapterError(
            f"secprd row-count mismatch: manifest={expected_rows}, read={source_rows}"
        )
    match = pd.concat(matches, ignore_index=True) if matches else pd.DataFrame()
    if len(match) != 1:
        raise VaultAdapterError(
            f"Expected one exact SPX spot row for {trade_date}; found {len(match)}"
        )
    close = pd.to_numeric(match["close"], errors="coerce")
    if (
        close.isna().any()
        or not np.isfinite(float(close.iloc[0]))
        or close.iloc[0] <= 0
    ):
        raise VaultAdapterError(f"Invalid exact SPX spot for {trade_date}")
    return float(close.iloc[0]), {
        "source_rows": source_rows,
        "trade_date_rows": date_rows,
        "secid_date_rows": len(match),
        "usable_close_rows": 1,
    }


def _read_zero_curve(
    path: Path, trade_date: str, expected_rows: int
) -> tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    source_rows = 0
    frames: list[pd.DataFrame] = []
    for chunk in _read_chunks(path, ["date", "days", "rate"]):
        source_rows += len(chunk)
        selected = chunk[chunk["date"].str.strip() == trade_date]
        if not selected.empty:
            frames.append(selected)
    if source_rows != expected_rows:
        raise VaultAdapterError(
            f"zerocd row-count mismatch: manifest={expected_rows}, read={source_rows}"
        )
    curve = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if curve.empty:
        raise VaultAdapterError(f"Missing exact zero curve for {trade_date}")
    days = pd.to_numeric(curve["days"], errors="coerce")
    rates = pd.to_numeric(curve["rate"], errors="coerce")
    if days.isna().any() or rates.isna().any():
        raise VaultAdapterError(f"Non-numeric zero curve for {trade_date}")
    if (
        not np.isfinite(days.to_numpy(dtype=float)).all()
        or not np.isfinite(rates.to_numpy(dtype=float)).all()
    ):
        raise VaultAdapterError(f"Non-finite zero curve for {trade_date}")
    if (days <= 0).any() or days.duplicated().any():
        raise VaultAdapterError(f"Ambiguous zero-curve tenors for {trade_date}")
    order = np.argsort(days.to_numpy(dtype=float))
    day_values = days.to_numpy(dtype=float)[order]
    decimal_rates = rates.to_numpy(dtype=float)[order] / 100.0
    return (
        day_values,
        decimal_rates,
        {
            "source_rows": source_rows,
            "trade_date_rows": len(curve),
            "usable_curve_rows": len(curve),
        },
    )


def _read_dividend(
    path: Path, secid: int, trade_date: str, expected_rows: int
) -> tuple[float, Dict[str, int]]:
    source_rows = 0
    date_rows = 0
    frames: list[pd.DataFrame] = []
    for chunk in _read_chunks(path, ["secid", "date", "rate"]):
        source_rows += len(chunk)
        date_mask = chunk["date"].str.strip() == trade_date
        date_rows += int(date_mask.sum())
        secids = pd.to_numeric(chunk["secid"], errors="coerce")
        selected = chunk[date_mask & (secids == secid)]
        if not selected.empty:
            frames.append(selected)
    if source_rows != expected_rows:
        raise VaultAdapterError(
            f"idxdvd row-count mismatch: manifest={expected_rows}, read={source_rows}"
        )
    match = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if len(match) != 1:
        raise VaultAdapterError(
            f"Expected one exact SPX dividend row for {trade_date}; found {len(match)}"
        )
    rate = pd.to_numeric(match["rate"], errors="coerce")
    if rate.isna().any() or not np.isfinite(float(rate.iloc[0])):
        raise VaultAdapterError(f"Invalid exact SPX dividend rate for {trade_date}")
    return float(rate.iloc[0]) / 100.0, {
        "source_rows": source_rows,
        "trade_date_rows": date_rows,
        "secid_date_rows": len(match),
        "usable_rate_rows": 1,
    }


def _read_quotes(
    path: Path,
    secid: int,
    trade_date: str,
    spot: float,
    curve_days: np.ndarray,
    curve_rates: np.ndarray,
    dividend: float,
    expected_rows: int,
) -> tuple[pd.DataFrame, Dict[str, int]]:
    source_rows = 0
    counts = {
        "trade_date_rows": 0,
        "secid_rows": 0,
        "call_rows": 0,
        "valid_market_rows": 0,
        "pipeline_tenor_rows": 0,
    }
    frames: list[pd.DataFrame] = []
    columns = [
        "secid",
        "date",
        "exdate",
        "cp_flag",
        "strike_price",
        "best_bid",
        "best_offer",
        "forward_price",
    ]
    trade_ts = pd.Timestamp(trade_date)
    for chunk in _read_chunks(path, columns):
        source_rows += len(chunk)
        date_mask = chunk["date"].str.strip() == trade_date
        counts["trade_date_rows"] += int(date_mask.sum())
        secids = pd.to_numeric(chunk["secid"], errors="coerce")
        secid_mask = date_mask & (secids == secid)
        counts["secid_rows"] += int(secid_mask.sum())
        call_mask = secid_mask & (chunk["cp_flag"].str.strip().str.upper() == "C")
        counts["call_rows"] += int(call_mask.sum())

        bids = pd.to_numeric(chunk["best_bid"], errors="coerce")
        offers = pd.to_numeric(chunk["best_offer"], errors="coerce")
        strikes = pd.to_numeric(chunk["strike_price"], errors="coerce")
        valid_market = (
            call_mask
            & np.isfinite(bids)
            & np.isfinite(offers)
            & np.isfinite(strikes)
            & (bids > 0)
            & (offers > bids)
            & (strikes > 0)
        )
        counts["valid_market_rows"] += int(valid_market.sum())
        selected = chunk[valid_market].copy()
        if selected.empty:
            continue
        expiries = pd.to_datetime(selected["exdate"], errors="coerce")
        if expiries.isna().any():
            raise VaultAdapterError(f"Invalid SPX option expiry for {trade_date}")
        dte = (expiries - trade_ts).dt.days
        tenor_mask = dte.between(MIN_PIPELINE_DTE_DAYS, MAX_PIPELINE_DTE_DAYS)
        selected = selected[tenor_mask].copy()
        dte = dte[tenor_mask]
        counts["pipeline_tenor_rows"] += len(selected)
        if selected.empty:
            continue
        selected["days_to_expiration"] = dte.to_numpy(dtype=int)
        frames.append(selected)

    if source_rows != expected_rows:
        raise VaultAdapterError(
            f"opprcd row-count mismatch: manifest={expected_rows}, read={source_rows}"
        )
    if not frames:
        raise VaultAdapterError(f"No exact usable SPX call quotes for {trade_date}")
    quotes = pd.concat(frames, ignore_index=True)
    quote_days = quotes["days_to_expiration"].to_numpy(dtype=float)
    if quote_days.min() < curve_days.min() or quote_days.max() > curve_days.max():
        raise VaultAdapterError(
            f"Zero curve does not bracket all pipeline quote tenors for {trade_date}"
        )

    quotes["strike"] = pd.to_numeric(quotes["strike_price"], errors="raise") / 1000.0
    quotes["best_bid"] = pd.to_numeric(quotes["best_bid"], errors="raise")
    quotes["best_offer"] = pd.to_numeric(quotes["best_offer"], errors="raise")
    quotes["forward_price"] = pd.to_numeric(quotes["forward_price"], errors="coerce")
    quotes["spot"] = spot
    quotes["rate"] = np.interp(quote_days, curve_days, curve_rates)
    quotes["divyield"] = dividend
    quotes["date"] = trade_date
    quotes["exdate"] = pd.to_datetime(quotes["exdate"], errors="raise")
    quotes["cp_flag"] = "C"
    quotes = quotes[
        [
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
        ]
    ].copy()
    quotes.attrs["fail_closed_real_data"] = True
    counts["source_rows"] = source_rows
    counts["returned_rows"] = len(quotes)
    return quotes, counts


def load_surface(
    root: Path | str,
    symbol: str,
    trade_date: str,
    *,
    snapshot: str = DEFAULT_SNAPSHOT,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Load one exact OptionMetrics surface and its restricted-local receipt."""

    root = Path(root).expanduser()
    if not root.is_absolute():
        root = root.resolve()
    symbol = _validate_component(symbol.strip().upper(), "ticker")
    if symbol != "SPX":
        raise VaultAdapterError(
            "The current vault research contract is SPX-only; refusing relabelled universe"
        )
    snapshot = _validate_component(snapshot, "snapshot")
    trade_date = _normalize_trade_date(trade_date)
    if not is_vault_root(root, snapshot):
        raise VaultAdapterError(
            f"WRDS local root is not the required partitioned vault snapshot: {root}"
        )

    paths = _source_paths(root, trade_date, snapshot)
    source_receipts: Dict[str, Dict[str, Any]] = {}
    source_stats: Dict[str, tuple[int, int]] = {}
    year = pd.Timestamp(trade_date).year
    for logical_table, (path, partition) in paths.items():
        manifest_table = (
            f"{logical_table}{year}"
            if logical_table in {"opprcd", "secprd"}
            else logical_table
        )
        receipt, source_stat = _validate_source(root, manifest_table, path, partition)
        source_receipts[logical_table] = receipt
        source_stats[logical_table] = source_stat

    expected = {
        table: int(receipt["source_manifest"]["item_rows"])
        for table, receipt in source_receipts.items()
    }
    secid, secnmd_counts = _resolve_secid(
        paths["secnmd"][0], symbol, trade_date, expected["secnmd"]
    )
    spot, secprd_counts = _read_spot(
        paths["secprd"][0], secid, trade_date, expected["secprd"]
    )
    curve_days, curve_rates, zerocd_counts = _read_zero_curve(
        paths["zerocd"][0], trade_date, expected["zerocd"]
    )
    dividend, idxdvd_counts = _read_dividend(
        paths["idxdvd"][0], secid, trade_date, expected["idxdvd"]
    )
    quotes, opprcd_counts = _read_quotes(
        paths["opprcd"][0],
        secid,
        trade_date,
        spot,
        curve_days,
        curve_rates,
        dividend,
        expected["opprcd"],
    )

    for table, (path, _) in paths.items():
        _assert_source_unchanged(path, source_stats[table], table)

    receipt: Dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "vault_root": str(root.resolve()),
        "dates": {"trade_date": trade_date, "month": trade_date[:7]},
        "universe": {
            "ticker": symbol,
            "resolved_secid": secid,
            "resolution": "latest secnmd.effect_date not after trade_date",
        },
        "source_format": "partitioned_csv_gz",
        "files": [source_receipts[name] for name in sorted(source_receipts)],
        "filter_row_counts": {
            "secnmd": secnmd_counts,
            "secprd": secprd_counts,
            "zerocd": zerocd_counts,
            "idxdvd": idxdvd_counts,
            "opprcd": opprcd_counts,
        },
        "transformations": {
            "strike_price": "divide source integer scale by 1000",
            "zero_curve": "linear interpolation by days-to-expiration; source percent divided by 100",
            "dividend_rate": "exact secid/date row; source percent divided by 100",
            "quote_filter": {
                "cp_flag": "C",
                "market": "best_bid > 0 and best_offer > best_bid and strike_price > 0",
                "days_to_expiration": [
                    MIN_PIPELINE_DTE_DAYS,
                    MAX_PIPELINE_DTE_DAYS,
                ],
            },
        },
    }
    quotes.attrs[RECEIPT_ATTR] = receipt
    quotes.attrs["fail_closed_real_data"] = True
    return quotes, receipt


def write_surface_receipts(path: Path, frames: Iterable[pd.DataFrame]) -> Path | None:
    """Atomically persist all vault receipts attached to a pipeline load."""

    frame_list = list(frames)
    receipts = [frame.attrs.get(RECEIPT_ATTR) for frame in frame_list]
    present = [receipt for receipt in receipts if receipt is not None]
    if not present:
        return None
    if len(present) != len(frame_list):
        raise VaultAdapterError(
            "Mixed vault/non-vault surfaces cannot share one real-data run"
        )
    payload = {
        "schema_version": RECEIPT_SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "surface_receipts": present,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)
    return path

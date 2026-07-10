#!/usr/bin/env python3
"""Synthetic mechanism tests for the restricted-local WRDS vault adapter."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wrds_pipeline import ingest_sppx_surface, pipeline, vault_adapter  # noqa: E402


TRADE_DATE = "2020-03-16"
SNAPSHOT = vault_adapter.DEFAULT_SNAPSHOT


def _write_csv_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise AssertionError("fixture rows must not be empty")
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _manifest_item(table: str, partition: str, path: Path, rows: int) -> dict[str, Any]:
    return {
        "table": table,
        "partition": partition,
        "path": str(path.resolve()),
        "status": "ok",
        "rows": rows,
        "size_bytes": path.stat().st_size,
    }


def _write_manifest(
    root: Path,
    name: str,
    items: list[dict[str, Any]],
    *,
    status: str = "ok",
) -> Path:
    path = root / "_manifests" / name / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": status, "items": items}, indent=2) + "\n")
    return path


def _build_fixture(
    root: Path,
    *,
    missing_dividend: bool = False,
    ambiguous_spot: bool = False,
    corrupt_quote_manifest_size: bool = False,
) -> dict[str, Path]:
    optionm = root / "raw" / "optionm"
    paths = {
        "opprcd": optionm
        / "opprcd2020"
        / f"snapshot={SNAPSHOT}"
        / f"day={TRADE_DATE}"
        / "data.csv.gz",
        "secprd": optionm
        / "secprd2020"
        / f"snapshot={SNAPSHOT}"
        / "month=2020-03"
        / "data.csv.gz",
        "secnmd": optionm / "secnmd" / f"snapshot={SNAPSHOT}" / "data.csv.gz",
        "zerocd": optionm / "zerocd" / f"snapshot={SNAPSHOT}" / "data.csv.gz",
        "idxdvd": optionm / "idxdvd" / f"snapshot={SNAPSHOT}" / "data.csv.gz",
    }

    quote_rows = [
        {
            "secid": 100,
            "date": TRADE_DATE,
            "exdate": "2020-04-15",
            "cp_flag": "C",
            "strike_price": 3000000,
            "best_bid": 100.0,
            "best_offer": 101.0,
            "forward_price": 3005.0,
        },
        {
            "secid": 100,
            "date": TRADE_DATE,
            "exdate": "2020-05-15",
            "cp_flag": "C",
            "strike_price": 3100000,
            "best_bid": 60.0,
            "best_offer": 61.0,
            "forward_price": 3010.0,
        },
        {
            "secid": 100,
            "date": TRADE_DATE,
            "exdate": "2020-03-26",
            "cp_flag": "C",
            "strike_price": 3000000,
            "best_bid": 20.0,
            "best_offer": 21.0,
            "forward_price": 3001.0,
        },
        {
            "secid": 100,
            "date": TRADE_DATE,
            "exdate": "2020-04-15",
            "cp_flag": "P",
            "strike_price": 3000000,
            "best_bid": 99.0,
            "best_offer": 100.0,
            "forward_price": 3005.0,
        },
        {
            "secid": 100,
            "date": TRADE_DATE,
            "exdate": "2020-04-15",
            "cp_flag": "C",
            "strike_price": 3000000,
            "best_bid": 0.0,
            "best_offer": 1.0,
            "forward_price": 3005.0,
        },
        {
            "secid": 200,
            "date": TRADE_DATE,
            "exdate": "2020-04-15",
            "cp_flag": "C",
            "strike_price": 3000000,
            "best_bid": 10.0,
            "best_offer": 11.0,
            "forward_price": 3005.0,
        },
        {
            "secid": 100,
            "date": "2020-03-17",
            "exdate": "2020-04-17",
            "cp_flag": "C",
            "strike_price": 3000000,
            "best_bid": 100.0,
            "best_offer": 101.0,
            "forward_price": 3005.0,
        },
    ]
    spot_rows = [
        {"secid": 100, "date": TRADE_DATE, "close": 3000.0},
        {"secid": 100, "date": "2020-03-17", "close": 3100.0},
        {"secid": 200, "date": TRADE_DATE, "close": 999.0},
    ]
    if ambiguous_spot:
        spot_rows.append({"secid": 100, "date": TRADE_DATE, "close": 3001.0})
    name_rows = [
        {"secid": 100, "effect_date": "2010-01-01", "ticker": "SPX"},
        {"secid": 999, "effect_date": "2021-01-01", "ticker": "SPX"},
        {"secid": 200, "effect_date": "2010-01-01", "ticker": "OTHER"},
    ]
    curve_rows = [
        {"date": TRADE_DATE, "days": 7, "rate": 0.50},
        {"date": TRADE_DATE, "days": 30, "rate": 0.60},
        {"date": TRADE_DATE, "days": 90, "rate": 0.90},
        {"date": "2020-03-17", "days": 30, "rate": 0.70},
    ]
    dividend_rows = [
        {"secid": 200 if missing_dividend else 100, "date": TRADE_DATE, "rate": 2.0},
        {"secid": 100, "date": "2020-03-17", "rate": 2.1},
    ]

    for key, rows in {
        "opprcd": quote_rows,
        "secprd": spot_rows,
        "secnmd": name_rows,
        "zerocd": curve_rows,
        "idxdvd": dividend_rows,
    }.items():
        _write_csv_gz(paths[key], rows)

    quote_item = _manifest_item(
        "opprcd2020", f"day={TRADE_DATE}", paths["opprcd"], len(quote_rows)
    )
    if corrupt_quote_manifest_size:
        quote_item["size_bytes"] += 1
    _write_manifest(root, "fixture_optionm_opprcd2020_day_csvgz", [quote_item])
    _write_manifest(
        root,
        "fixture_optionm_secprd2020_month_csvgz",
        [
            _manifest_item(
                "secprd2020", "month=2020-03", paths["secprd"], len(spot_rows)
            )
        ],
    )
    _write_manifest(
        root,
        "fixture_optionm_secnmd_csvgz",
        [_manifest_item("secnmd", "table", paths["secnmd"], len(name_rows))],
        status="operator_paused_at_boundary",
    )
    _write_manifest(
        root,
        "fixture_optionm_zerocd_csvgz",
        [_manifest_item("zerocd", "table", paths["zerocd"], len(curve_rows))],
        status="operator_paused_at_boundary",
    )
    _write_manifest(
        root,
        "fixture_optionm_idxdvd_csvgz",
        [_manifest_item("idxdvd", "table", paths["idxdvd"], len(dividend_rows))],
        status="operator_paused_at_boundary",
    )
    return paths


def _expect_error(root: Path, needle: str) -> None:
    try:
        vault_adapter.load_surface(root, "SPX", TRADE_DATE)
    except vault_adapter.VaultAdapterError as exc:
        if needle not in str(exc):
            raise AssertionError(f"Expected {needle!r}; got {exc!r}") from exc
    else:
        raise AssertionError(f"Expected VaultAdapterError containing {needle!r}")


def _test_exact_load_and_receipt(root: Path) -> None:
    paths = _build_fixture(root)
    try:
        vault_adapter.load_surface(root, "OTHER", TRADE_DATE)
    except vault_adapter.VaultAdapterError as exc:
        if "SPX-only" not in str(exc):
            raise
    else:
        raise AssertionError("adapter accepted a universe the pipeline would relabel")
    quotes, receipt = vault_adapter.load_surface(root, "SPX", TRADE_DATE)
    if len(quotes) != 2:
        raise AssertionError(f"Expected two pipeline-eligible calls; got {len(quotes)}")
    np.testing.assert_allclose(quotes["spot"], [3000.0, 3000.0])
    np.testing.assert_allclose(quotes["divyield"], [0.02, 0.02])
    np.testing.assert_allclose(quotes["rate"], [0.006, 0.0075], atol=1e-12)
    if quotes.attrs.get("fail_closed_real_data") is not True:
        raise AssertionError("real-data fail-closed marker was not retained")
    if receipt["snapshot"] != SNAPSHOT:
        raise AssertionError("receipt snapshot drifted")
    if receipt["universe"]["resolved_secid"] != 100:
        raise AssertionError("as-of resolution used the future-poison secid")
    counts = receipt["filter_row_counts"]
    if counts["opprcd"]["returned_rows"] != 2:
        raise AssertionError("receipt quote counts are not exact")
    if counts["secnmd"]["ticker_rows"] != 2:
        raise AssertionError("receipt name-resolution counts are not exact")
    files = {entry["table"]: entry for entry in receipt["files"]}
    quote_receipt = files["opprcd2020"]
    expected_hash = hashlib.sha256(paths["opprcd"].read_bytes()).hexdigest()
    if quote_receipt["sha256"] != expected_hash:
        raise AssertionError("receipt did not bind the exact compressed quote file")
    if quote_receipt["source_manifest"]["item_status"] != "ok":
        raise AssertionError("receipt did not bind an ok acquisition item")

    loaded, source = ingest_sppx_surface.load_surface(
        "SPX", TRADE_DATE, local_root=root
    )
    if source != "local" or len(loaded) != 2:
        raise AssertionError("ingestion did not route through the vault adapter")
    with tempfile.TemporaryDirectory() as receipt_tmp:
        out = Path(receipt_tmp) / "source_receipt.json"
        written = ingest_sppx_surface.write_source_receipts(out, (loaded, loaded))
        if written != out or not out.is_file():
            raise AssertionError("source receipt was not written atomically")
        payload = json.loads(out.read_text())
        if len(payload.get("surface_receipts", [])) != 2:
            raise AssertionError("combined source receipt lost a surface")


def _test_dateset_aborts_instead_of_emitting_partial_result(root: Path) -> None:
    _build_fixture(root)
    dateset = root / "dateset.json"
    dateset.write_text(
        json.dumps(
            {
                "panel_id": "synthetic_fail_closed_panel",
                "dates": [
                    {
                        "trade_date": TRADE_DATE,
                        "next_trade_date": "2020-03-17",
                    }
                ],
            }
        )
    )
    try:
        pipeline.run_dateset(
            "SPX",
            dateset,
            use_sample=False,
            fast=True,
            output_root=root / "out",
            local_root=root,
        )
    except RuntimeError as exc:
        if "Fail-closed local-vault dateset aborted" not in str(exc):
            raise
    else:
        raise AssertionError("local-vault dateset emitted a partial result")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _test_exact_load_and_receipt(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _build_fixture(root, missing_dividend=True)
        _expect_error(root, "Expected one exact SPX dividend row")
        try:
            ingest_sppx_surface.load_surface("SPX", TRADE_DATE, local_root=root)
        except vault_adapter.VaultAdapterError:
            pass
        else:
            raise AssertionError(
                "explicit local failure silently fell back to sample data"
            )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _build_fixture(root, ambiguous_spot=True)
        _expect_error(root, "Expected one exact SPX spot row")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _build_fixture(root, corrupt_quote_manifest_size=True)
        _expect_error(root, "Size mismatch for opprcd2020")
    with tempfile.TemporaryDirectory() as tmp:
        _test_dateset_aborts_instead_of_emitting_partial_result(Path(tmp))


if __name__ == "__main__":
    main()

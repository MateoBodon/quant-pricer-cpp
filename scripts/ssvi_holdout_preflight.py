#!/usr/bin/env python3
"""Validate the sealed SSVI holdout and vault metadata without opening outcomes.

This command hashes compressed vault objects and checks their acquisition
manifests. It never decompresses a source file, parses an option row, calibrates
a model, or computes a performance metric. Raw vault paths are never emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wrds_pipeline import pipeline, vault_adapter  # noqa: E402

CONTRACT_PATH = REPO_ROOT / "configs" / "ssvi_temporal_holdout_v1.json"
PANEL_PATH = REPO_ROOT / "wrds_pipeline_dates_ssvi_holdout_v1.yaml"
SOURCE_PANEL_PATH = REPO_ROOT / "wrds_pipeline_dates_panel_resume_v2.yaml"
CONTRACT_ID = "ssvi_temporal_holdout_v1"
EXPECTED_CONTRACT_SHA256 = (
    "2b042a32bbaad3f7a83be88721e7b0c4c1d0f50db417a88209c8de1342c276a0"
)
EXPECTED_PANEL_SHA256 = (
    "301aced837431eff2276067d08e12581918d85a498d8e9d0ef33e338a69dc974"
)
EXPECTED_SOURCE_PANEL_SHA256 = (
    "51c0cb040a8f45d12bb7db5c1432b6371ff6d08402def442aee1709643af0a3c"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _entries(payload: Dict[str, object]) -> list[list[str]]:
    raw_entries = payload.get("dates")
    if not isinstance(raw_entries, list):
        raise RuntimeError("sealed panel dates must be a list")
    result = []
    for item in raw_entries:
        if not isinstance(item, dict):
            raise RuntimeError("sealed panel entry must be a mapping")
        result.append(
            [
                str(item.get("trade_date", "")),
                str(item.get("next_trade_date", "")),
                str(item.get("label", "")),
                str(item.get("regime", "")),
            ]
        )
    return result


def validate_contract(
    contract_path: Path = CONTRACT_PATH,
    panel_path: Path = PANEL_PATH,
    source_panel_path: Path = SOURCE_PANEL_PATH,
) -> Dict[str, Any]:
    if _sha256(contract_path) != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError("sealed SSVI holdout contract hash changed")
    contract = json.loads(contract_path.read_text())
    if contract.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("unexpected SSVI holdout contract id")
    if contract.get("status") != "sealed_pre_outcome":
        raise RuntimeError("SSVI holdout contract is not sealed pre-outcome")
    panel_sha = _sha256(panel_path)
    source_panel_sha = _sha256(source_panel_path)
    if panel_sha != EXPECTED_PANEL_SHA256:
        raise RuntimeError("sealed SSVI holdout panel hash changed")
    if source_panel_sha != EXPECTED_SOURCE_PANEL_SHA256:
        raise RuntimeError("parent resume panel hash changed")
    panel_contract = contract.get("panel")
    if not isinstance(panel_contract, dict):
        raise RuntimeError("contract panel block is missing")
    if panel_contract.get("sha256") != panel_sha:
        raise RuntimeError("contract does not bind the sealed panel hash")
    if panel_contract.get("source_panel_sha256") != source_panel_sha:
        raise RuntimeError("contract does not bind the parent panel hash")

    panel_payload = pipeline._load_dateset_payload(panel_path)
    if panel_payload.get("panel_id") != CONTRACT_ID:
        raise RuntimeError("sealed panel id changed")
    panel_entries = _entries(panel_payload)
    if panel_entries != panel_contract.get("entries"):
        raise RuntimeError("sealed panel entries differ from the contract")
    if len(panel_entries) != 12 or len({tuple(item[:2]) for item in panel_entries}) != 12:
        raise RuntimeError("sealed panel must contain twelve unique date pairs")

    source_payload = pipeline._load_dateset_payload(source_panel_path)
    source_entries = _entries(source_payload)
    qanchors = [item for item in source_entries if item[2].startswith("qanchor-")]
    excluded = [item[:2] for item in source_entries if not item[2].startswith("qanchor-")]
    if qanchors != panel_entries:
        raise RuntimeError("sealed panel is not the exact parent qanchor subset")
    if excluded != [
        ["2020-03-16", "2020-03-17"],
        ["2020-03-17", "2020-03-18"],
    ]:
        raise RuntimeError("parent-panel exclusion rule changed")

    frozen = contract.get("frozen_implementation")
    if not isinstance(frozen, dict) or not frozen:
        raise RuntimeError("contract frozen implementation block is missing")
    for relative, expected in frozen.items():
        path = REPO_ROOT / str(relative)
        if not path.is_file() or _sha256(path) != expected:
            raise RuntimeError(f"frozen implementation changed: {relative}")
    return contract


def _safe_source_record(
    root: Path,
    logical_table: str,
    manifest_table: str,
    source_path: Path,
    partition: str,
) -> Dict[str, object]:
    try:
        before = source_path.stat()
        binding = vault_adapter._load_manifest_binding(
            root,
            manifest_table,
            source_path,
        )
        source_sha = _sha256(source_path)
        after = source_path.stat()
    except (OSError, vault_adapter.VaultAdapterError) as exc:
        raise RuntimeError(
            f"metadata validation failed for {manifest_table}/{partition}: "
            f"{type(exc).__name__}"
        ) from None
    if before.st_size <= 0 or int(binding["item_rows"]) <= 0:
        raise RuntimeError(
            f"empty source metadata for {manifest_table}/{partition}"
        )
    if (before.st_size, before.st_mtime_ns) != (
        after.st_size,
        after.st_mtime_ns,
    ):
        raise RuntimeError(
            f"source changed during metadata validation: {manifest_table}/{partition}"
        )
    return {
        "logical_table": logical_table,
        "manifest_table": manifest_table,
        "partition": partition,
        "bytes": int(before.st_size),
        "sha256": source_sha,
        "source_manifest_sha256": str(binding["sha256"]),
        "source_manifest_overall_status": binding["overall_status"],
        "source_manifest_item_status": binding["item_status"],
        "source_manifest_rows": int(binding["item_rows"]),
        "source_manifest_size_bytes": int(binding["item_size_bytes"]),
    }


def build_inventory(contract: Dict[str, Any], root: Path) -> Dict[str, object]:
    if not root.is_absolute() or not vault_adapter.is_vault_root(root):
        raise RuntimeError("WRDS_LOCAL_ROOT is not the required vault snapshot")
    entries = contract["panel"]["entries"]
    surface_dates = sorted({value for item in entries for value in item[:2]})
    if len(surface_dates) != 24:
        raise RuntimeError("sealed panel must resolve to twenty-four surface dates")

    records_by_path: Dict[Path, Dict[str, object]] = {}
    date_bindings = []
    for trade_date in surface_dates:
        paths = vault_adapter._source_paths(
            root,
            trade_date,
            vault_adapter.DEFAULT_SNAPSHOT,
        )
        bindings = []
        year = int(trade_date[:4])
        for logical_table, (source_path, partition) in paths.items():
            manifest_table = (
                f"{logical_table}{year}"
                if logical_table in {"opprcd", "secprd"}
                else logical_table
            )
            resolved = source_path.resolve()
            if resolved not in records_by_path:
                records_by_path[resolved] = _safe_source_record(
                    root,
                    logical_table,
                    manifest_table,
                    source_path,
                    partition,
                )
            record = records_by_path[resolved]
            bindings.append(
                {
                    "logical_table": logical_table,
                    "manifest_table": manifest_table,
                    "partition": partition,
                    "sha256": record["sha256"],
                }
            )
        date_bindings.append({"trade_date": trade_date, "sources": bindings})

    records = sorted(
        records_by_path.values(),
        key=lambda item: (str(item["logical_table"]), str(item["partition"])),
    )
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    inventory_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    table_counts = Counter(str(item["logical_table"]) for item in records)
    manifest_hashes = {str(item["source_manifest_sha256"]) for item in records}
    payload: Dict[str, object] = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "status": "metadata_inventory_computed",
        "source_access": "compressed_hash_and_manifest_metadata_only_no_decompression_or_rows",
        "snapshot": vault_adapter.DEFAULT_SNAPSHOT,
        "panel_sha256": EXPECTED_PANEL_SHA256,
        "date_pair_count": 12,
        "unique_surface_date_count": len(surface_dates),
        "unique_source_file_count": len(records),
        "unique_acquisition_manifest_count": len(manifest_hashes),
        "total_compressed_bytes": sum(int(item["bytes"]) for item in records),
        "table_file_counts": dict(sorted(table_counts.items())),
        "inventory_sha256": inventory_sha,
        "files": records,
        "date_bindings": date_bindings,
    }
    expected_inventory = contract.get("inventory")
    if expected_inventory is not None:
        if not isinstance(expected_inventory, dict):
            raise RuntimeError("contract inventory block must be a mapping")
        checks = {
            "unique_source_file_count": payload["unique_source_file_count"],
            "unique_acquisition_manifest_count": payload[
                "unique_acquisition_manifest_count"
            ],
            "total_compressed_bytes": payload["total_compressed_bytes"],
            "table_file_counts": payload["table_file_counts"],
            "inventory_sha256": payload["inventory_sha256"],
        }
        for key, actual in checks.items():
            if expected_inventory.get(key) != actual:
                raise RuntimeError(f"sealed inventory mismatch: {key}")
        payload["status"] = "sealed_manifest_hash_complete"
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--panel", type=Path, default=PANEL_PATH)
    parser.add_argument("--source-panel", type=Path, default=SOURCE_PANEL_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-contract-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contract = validate_contract(args.contract, args.panel, args.source_panel)
    if args.check_contract_only:
        print(
            json.dumps(
                {
                    "contract_id": CONTRACT_ID,
                    "date_pair_count": 12,
                    "status": "sealed_contract_valid",
                },
                sort_keys=True,
            )
        )
        return
    if args.output is None:
        raise RuntimeError("--output is required for metadata inventory")
    raw_root = os.environ.get("WRDS_LOCAL_ROOT", "").strip()
    if not raw_root:
        raise RuntimeError("WRDS_LOCAL_ROOT is required for metadata inventory")
    inventory = build_inventory(contract, Path(raw_root).expanduser())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: inventory[key] for key in (
        "status",
        "date_pair_count",
        "unique_surface_date_count",
        "unique_source_file_count",
        "unique_acquisition_manifest_count",
        "total_compressed_bytes",
        "table_file_counts",
        "inventory_sha256",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()

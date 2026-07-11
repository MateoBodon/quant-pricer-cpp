#!/usr/bin/env python3
"""Execute the published SSVI temporal holdout exactly once.

All contract, publication, inventory, run-manifest, and source-receipt checks
complete before any aggregate surface CSV is opened. The command does not
evaluate hedging or strategy returns and writes aggregate diagnostics only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ssvi_five_date_panel import (  # noqa: E402
    _paired_ssvi_comparison,
    _stability,
    _winner_counts,
)
from ssvi_holdout_preflight import (  # noqa: E402
    CONTRACT_ID,
    CONTRACT_PATH,
    EXPECTED_CONTRACT_SHA256,
    EXPECTED_PANEL_SHA256,
    PANEL_PATH,
    _sha256 as _file_sha256,
    validate_contract,
)
from ssvi_development_benchmark import _date_result  # noqa: E402

BRANCH_NAME = "recovery/quant-pre-v3-20260710"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_INVENTORY_SHA256 = (
    "ca7fff944cc94c988e5c0b4d34cf7d99c2c46d9a8043c80fde297a464e818ca7"
)
CONSUMED_MARKER = ".ssvi_temporal_holdout_v1_consumed.json"


def _iso_datetime(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"{label} must be an ISO timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"{label} must be an ISO timestamp") from exc


def validate_publication_receipt(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text())
    required = {
        "status": "published_exact_tree_readback",
        "repository": "MateoBodon/quant-pricer-cpp",
        "branch": BRANCH_NAME,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "panel_sha256": EXPECTED_PANEL_SHA256,
        "inventory_sha256": EXPECTED_INVENTORY_SHA256,
        "authoritative_readback": True,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise RuntimeError(f"publication receipt mismatch: {key}")
    for key in ("remote_tree_sha", "remote_commit_sha"):
        value = payload.get(key)
        if not isinstance(value, str) or not HEX40.fullmatch(value):
            raise RuntimeError(f"publication receipt has invalid {key}")
    inventory_receipt_sha = payload.get("inventory_receipt_sha256")
    if not isinstance(inventory_receipt_sha, str) or not HEX64.fullmatch(
        inventory_receipt_sha
    ):
        raise RuntimeError("publication receipt has invalid inventory receipt hash")
    _iso_datetime(payload.get("published_at_utc"), "published_at_utc")
    return payload


def validate_inventory_receipt(
    path: Path,
    contract: Dict[str, Any],
) -> Dict[str, Any]:
    payload = json.loads(path.read_text())
    if payload.get("status") != "sealed_manifest_hash_complete":
        raise RuntimeError("inventory receipt is not sealed and complete")
    if payload.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("inventory receipt contract id changed")
    if payload.get("panel_sha256") != EXPECTED_PANEL_SHA256:
        raise RuntimeError("inventory receipt panel hash changed")
    inventory = contract.get("inventory")
    if not isinstance(inventory, dict):
        raise RuntimeError("contract inventory block is missing")
    for key in (
        "unique_surface_date_count",
        "unique_source_file_count",
        "unique_acquisition_manifest_count",
        "total_compressed_bytes",
        "table_file_counts",
        "inventory_sha256",
    ):
        if payload.get(key) != inventory.get(key):
            raise RuntimeError(f"inventory receipt mismatch: {key}")
    files = payload.get("files")
    if not isinstance(files, list):
        raise RuntimeError("inventory receipt files block is missing")
    for item in files:
        if (
            not isinstance(item, dict)
            or item.get("source_manifest_item_status") != "ok"
            or int(item.get("bytes", 0)) <= 0
            or int(item.get("source_manifest_rows", 0)) <= 0
            or item.get("bytes") != item.get("source_manifest_size_bytes")
        ):
            raise RuntimeError("inventory receipt contains invalid source metadata")
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"))
    computed_inventory_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if computed_inventory_sha != inventory.get("inventory_sha256"):
        raise RuntimeError("inventory receipt file digest changed")
    return payload


def validate_inventory_publication_binding(
    publication: Dict[str, Any],
    inventory_path: Path,
) -> None:
    if publication.get("inventory_receipt_sha256") != _file_sha256(inventory_path):
        raise RuntimeError("publication receipt does not bind the inventory receipt")


def consume_once(run_root: Path, publication: Dict[str, Any]) -> Path:
    marker = run_root / CONSUMED_MARKER
    payload = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "remote_commit_sha": publication["remote_commit_sha"],
        "remote_tree_sha": publication["remote_tree_sha"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "consumed_unknown_until_result_receipt",
    }
    try:
        with marker.open("x") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        raise RuntimeError(
            "sealed holdout was already consumed; reconcile the existing outcome"
        ) from None
    return marker


def _manifest_after_publication(
    manifest: Dict[str, Any],
    publication: Dict[str, Any],
) -> None:
    manifest_time = _iso_datetime(manifest.get("generated_at"), "manifest generated_at")
    publication_time = _iso_datetime(
        publication.get("published_at_utc"),
        "published_at_utc",
    )
    if manifest_time < publication_time:
        raise RuntimeError("holdout run manifest predates contract publication")


def validate_run_root(
    run_root: Path,
    contract: Dict[str, Any],
    publication: Dict[str, Any],
    inventory_receipt: Dict[str, Any],
) -> None:
    manifest_path = run_root / "manifest_local.json"
    if not manifest_path.is_file():
        raise RuntimeError("holdout run manifest is missing")
    manifest = json.loads(manifest_path.read_text())
    _manifest_after_publication(manifest, publication)
    dateset_runs = manifest.get("runs", {}).get("wrds_dateset", [])
    if not isinstance(dateset_runs, list) or len(dateset_runs) != 1:
        raise RuntimeError("holdout run must contain exactly one dateset receipt")
    dateset = dateset_runs[0]
    if dateset.get("panel_id") != CONTRACT_ID:
        raise RuntimeError("holdout run panel id changed")
    inputs = dateset.get("dateset_inputs", [])
    if not isinstance(inputs, list) or not any(
        item.get("sha256") == EXPECTED_PANEL_SHA256
        for item in inputs
        if isinstance(item, dict)
    ):
        raise RuntimeError("holdout run does not bind the sealed panel hash")
    pipeline_runs = manifest.get("runs", {}).get("wrds_pipeline", [])
    if not isinstance(pipeline_runs, list) or len(pipeline_runs) != 12:
        raise RuntimeError("holdout run must contain twelve pipeline receipts")

    entries = contract["panel"]["entries"]
    expected_trade_dates = [item[0] for item in entries]
    observed_trade_dates = [str(item.get("trade_date")) for item in pipeline_runs]
    if observed_trade_dates != expected_trade_dates:
        raise RuntimeError("holdout pipeline receipt order or dates changed")
    if any(item.get("panel_id") != CONTRACT_ID for item in pipeline_runs):
        raise RuntimeError("holdout pipeline receipt panel id changed")

    per_date_root = run_root / "per_date"
    actual_dirs = sorted(
        path.name for path in per_date_root.iterdir() if path.is_dir()
    )
    if actual_dirs != sorted(expected_trade_dates):
        raise RuntimeError("holdout run has missing or extra per-date directories")

    inventory_files = {
        (
            str(item["manifest_table"]),
            str(item["partition"]),
            str(item["sha256"]),
            str(item["source_manifest_sha256"]),
        )
        for item in inventory_receipt.get("files", [])
    }
    observed_source_files = set()
    for trade_date, next_trade_date, _, _ in entries:
        date_root = per_date_root / trade_date
        receipt_path = date_root / "source_receipt.json"
        today_path = date_root / f"spx_{trade_date}_surface.csv"
        next_path = date_root / f"spx_{next_trade_date}_surface.csv"
        if not receipt_path.is_file() or not today_path.is_file() or not next_path.is_file():
            raise RuntimeError(f"holdout aggregate inputs missing for {trade_date}")
        receipt = json.loads(receipt_path.read_text())
        surface_receipts = receipt.get("surface_receipts", [])
        receipt_dates = [
            item.get("dates", {}).get("trade_date") for item in surface_receipts
        ]
        if receipt_dates != [trade_date, next_trade_date]:
            raise RuntimeError(f"source receipt date mismatch for {trade_date}")
        for surface_receipt in surface_receipts:
            for item in surface_receipt.get("files", []):
                source_manifest = item.get("source_manifest", {})
                observed_source_files.add(
                    (
                        str(item.get("table")),
                        str(item.get("partition")),
                        str(item.get("sha256")),
                        str(source_manifest.get("sha256")),
                    )
                )
    if observed_source_files != inventory_files:
        raise RuntimeError("holdout run source hashes differ from sealed inventory")


def _primary_gate(
    per_date: list[Dict[str, object]],
    all_ssvi_valid: bool,
) -> Dict[str, object]:
    comparisons = {}
    all_pass = all_ssvi_valid
    for comparator in ("heston", "tenor_flat_bs"):
        relative_changes = []
        win_dates = []
        for item in per_date:
            ssvi_value = float(
                item["models"]["ssvi"]["oos"]["price_mae_ticks"]
            )
            comparator_value = float(
                item["models"][comparator]["oos"]["price_mae_ticks"]
            )
            if not (
                math.isfinite(ssvi_value)
                and math.isfinite(comparator_value)
                and comparator_value > 0.0
            ):
                raise RuntimeError("nonfinite primary holdout metric")
            relative_changes.append(
                (ssvi_value / comparator_value - 1.0) * 100.0
            )
            if ssvi_value < comparator_value:
                win_dates.append(str(item["trade_date"]))
        wins = len(win_dates)
        median_change = float(np.median(relative_changes))
        sign_probability = sum(
            math.comb(len(per_date), count)
            for count in range(wins, len(per_date) + 1)
        ) / float(2 ** len(per_date))
        passed = wins >= 10 and median_change < 0.0
        all_pass = all_pass and passed
        comparisons[comparator] = {
            "date_count": len(per_date),
            "ssvi_win_count": wins,
            "ssvi_win_dates": win_dates,
            "median_relative_change_percent": median_change,
            "mean_relative_change_percent": float(np.mean(relative_changes)),
            "one_sided_exact_sign_probability": sign_probability,
            "passed": passed,
        }
    return {
        "all_ssvi_analytic_numerical_finite_and_quantlib_gates_pass": (
            all_ssvi_valid
        ),
        "comparisons": comparisons,
        "passed": all_pass,
    }


def execute(
    run_root: Path,
    contract: Dict[str, Any],
) -> Dict[str, object]:
    entries = contract["panel"]["entries"]
    per_date = [
        _date_result(
            run_root,
            trade_date,
            next_trade_date,
            label=label,
            regime=regime,
            include_hedge=False,
        )
        for trade_date, next_trade_date, label, regime in entries
    ]
    all_ssvi_valid = all(
        item["models"]["ssvi"]["promotion_status"] == "eligible"
        and item["models"]["ssvi"]["calibration_diagnostics"]["arbitrage"][
            "analytic_sufficient_conditions_pass"
        ]
        and item["models"]["ssvi"]["calibration_diagnostics"]["arbitrage"][
            "numerical_static_arbitrage_pass"
        ]
        and item["models"]["ssvi"]["independent_reference"]["status"] == "valid"
        and item["models"]["ssvi"]["oos"]["invalid_rows"] == 0
        for item in per_date
    )
    primary = _primary_gate(per_date, all_ssvi_valid)
    payload: Dict[str, object] = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "panel_sha256": EXPECTED_PANEL_SHA256,
        "status": "confirmed" if primary["passed"] else "not_confirmed",
        "claim_scope": "ssvi_unseen_not_dataset_blind_twelve_pair_temporal_holdout",
        "data_policy": "aggregate_only_no_option_rows_or_parameters",
        "input_run_id": run_root.name,
        "date_count": len(per_date),
        "insample_surface_rows": sum(
            int(item["insample_surface_rows"]) for item in per_date
        ),
        "oos_surface_rows": sum(int(item["oos_surface_rows"]) for item in per_date),
        "primary_gate": primary,
        "winner_counts": _winner_counts(per_date),
        "stability": _stability(per_date),
        "paired_ssvi_comparison": _paired_ssvi_comparison(per_date),
        "heston_promotion_status_by_date": {
            str(item["trade_date"]): item["models"]["heston"]["promotion_status"]
            for item in per_date
        },
        "hedge_evaluation": "not_evaluated",
        "per_date": per_date,
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--inventory-receipt", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--panel", type=Path, default=PANEL_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise RuntimeError("sealed holdout output already exists; refusing a rerun")
    contract = validate_contract(args.contract, args.panel)
    publication = validate_publication_receipt(args.publication_receipt)
    inventory = validate_inventory_receipt(args.inventory_receipt, contract)
    validate_inventory_publication_binding(publication, args.inventory_receipt)
    run_root = args.run_root.resolve()
    validate_run_root(run_root, contract, publication, inventory)
    consume_once(run_root, publication)
    payload = execute(run_root, contract)
    payload["publication_provenance"] = {
        "remote_commit_sha": publication["remote_commit_sha"],
        "remote_tree_sha": publication["remote_tree_sha"],
        "published_at_utc": publication["published_at_utc"],
        "inventory_receipt_sha256": publication["inventory_receipt_sha256"],
        "inventory_sha256": inventory["inventory_sha256"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(args.output)


if __name__ == "__main__":
    main()

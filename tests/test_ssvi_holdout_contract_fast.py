#!/usr/bin/env python3
"""Fail-fast guards for the sealed SSVI temporal holdout."""
from __future__ import annotations

import json
import hashlib
import math
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (REPO_ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ssvi_holdout_preflight import (  # noqa: E402
    CONTRACT_ID,
    EXPECTED_CONTRACT_SHA256,
    EXPECTED_PANEL_SHA256,
    validate_contract,
)
from ssvi_sealed_holdout import (  # noqa: E402
    _primary_gate,
    consume_once,
    validate_inventory_receipt,
    validate_inventory_publication_binding,
    validate_publication_receipt,
)


def _date_item(index: int, ssvi: float, heston: float, bs: float) -> dict:
    return {
        "trade_date": f"2025-01-{index + 1:02d}",
        "models": {
            "ssvi": {"oos": {"price_mae_ticks": ssvi}},
            "heston": {"oos": {"price_mae_ticks": heston}},
            "tenor_flat_bs": {"oos": {"price_mae_ticks": bs}},
        },
    }


def _expect_runtime_error(fn) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError("expected fail-closed RuntimeError")


def main() -> None:
    contract = validate_contract()
    if contract["contract_id"] != CONTRACT_ID:
        raise AssertionError("contract id changed")
    if contract["panel"]["date_pair_count"] != 12:
        raise AssertionError("holdout date count changed")
    if contract["panel"]["sha256"] != EXPECTED_PANEL_SHA256:
        raise AssertionError("holdout panel hash changed")
    if contract["primary_gate"][
        "oos_price_mae_ticks_ssvi_wins_vs_heston_at_least"
    ] != 10:
        raise AssertionError("Heston primary win threshold changed")
    if contract["primary_gate"][
        "oos_price_mae_ticks_ssvi_wins_vs_tenor_flat_bs_at_least"
    ] != 10:
        raise AssertionError("BS primary win threshold changed")
    if contract["primary_gate"]["ties_count_as_wins"]:
        raise AssertionError("ties must not count as wins")

    ten_win_panel = [
        _date_item(index, 1.0, 2.0, 3.0)
        if index < 10
        else _date_item(index, 4.0, 2.0, 3.0)
        for index in range(12)
    ]
    primary = _primary_gate(ten_win_panel, True)
    if not primary["passed"]:
        raise AssertionError("the exact 10/12 primary gate must pass")
    expected_probability = 79.0 / 4096.0
    for comparison in primary["comparisons"].values():
        if not math.isclose(
            comparison["one_sided_exact_sign_probability"],
            expected_probability,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise AssertionError("exact sign probability changed")

    nine_win_panel = [
        _date_item(index, 1.0, 2.0, 3.0)
        if index < 9
        else _date_item(index, 4.0, 2.0, 3.0)
        for index in range(12)
    ]
    if _primary_gate(nine_win_panel, True)["passed"]:
        raise AssertionError("9/12 must not confirm the holdout")
    if _primary_gate(ten_win_panel, False)["passed"]:
        raise AssertionError("failed numerical gates must block confirmation")

    publication = {
        "status": "published_exact_tree_readback",
        "repository": "MateoBodon/quant-pricer-cpp",
        "branch": "recovery/quant-pre-v3-20260710",
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "panel_sha256": EXPECTED_PANEL_SHA256,
        "inventory_sha256": contract["inventory"]["inventory_sha256"],
        "remote_tree_sha": "a" * 40,
        "remote_commit_sha": "b" * 40,
        "published_at_utc": "2026-07-11T20:15:00Z",
        "authoritative_readback": True,
        "inventory_receipt_sha256": "0" * 64,
    }
    test_contract = json.loads(json.dumps(contract))
    inventory_files = [
        {
            "logical_table": "opprcd",
            "manifest_table": "opprcd2025",
            "partition": "day=2025-01-02",
            "bytes": 100,
            "sha256": "c" * 64,
            "source_manifest_sha256": "d" * 64,
            "source_manifest_overall_status": "ok",
            "source_manifest_item_status": "ok",
            "source_manifest_rows": 10,
            "source_manifest_size_bytes": 100,
        }
    ]
    inventory_digest = hashlib.sha256(
        json.dumps(
            inventory_files,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    test_contract["inventory"]["inventory_sha256"] = inventory_digest
    inventory = {
        "status": "sealed_manifest_hash_complete",
        "contract_id": CONTRACT_ID,
        "panel_sha256": EXPECTED_PANEL_SHA256,
        **{
            key: test_contract["inventory"][key]
            for key in (
                "unique_surface_date_count",
                "unique_source_file_count",
                "unique_acquisition_manifest_count",
                "total_compressed_bytes",
                "table_file_counts",
                "inventory_sha256",
            )
        },
        "files": inventory_files,
    }
    with tempfile.TemporaryDirectory(prefix="ssvi-holdout-contract-") as tmp:
        publication_path = Path(tmp) / "publication.json"
        inventory_path = Path(tmp) / "inventory.json"
        inventory_path.write_text(json.dumps(inventory))
        from ssvi_holdout_preflight import _sha256 as _file_sha256

        publication["inventory_receipt_sha256"] = _file_sha256(inventory_path)
        publication_path.write_text(json.dumps(publication))
        validate_publication_receipt(publication_path)
        validate_inventory_receipt(inventory_path, test_contract)
        validate_inventory_publication_binding(publication, inventory_path)

        publication["authoritative_readback"] = False
        publication_path.write_text(json.dumps(publication))
        _expect_runtime_error(lambda: validate_publication_receipt(publication_path))

        inventory["unique_source_file_count"] = 38
        inventory_path.write_text(json.dumps(inventory))
        _expect_runtime_error(
            lambda: validate_inventory_receipt(inventory_path, test_contract)
        )
        _expect_runtime_error(
            lambda: validate_inventory_publication_binding(
                publication,
                inventory_path,
            )
        )

        run_root = Path(tmp) / "run"
        run_root.mkdir()
        consume_once(run_root, publication)
        _expect_runtime_error(lambda: consume_once(run_root, publication))

    preflight_source = (SCRIPTS_DIR / "ssvi_holdout_preflight.py").read_text()
    if "read_csv" in preflight_source or "gzip.open" in preflight_source:
        raise AssertionError("metadata preflight must not parse compressed outcomes")


if __name__ == "__main__":
    main()

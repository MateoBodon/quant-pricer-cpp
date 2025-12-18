#!/usr/bin/env python3
"""FAST test: generate metrics snapshot from committed artifacts.

This test ensures the snapshot script runs and the outputs contain the
required top-level blocks with status fields, guarding against silent
schema drift in artifacts.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "docs" / "artifacts"
JSON_OUT = ARTIFACTS / "metrics_summary.json"
MD_OUT = ARTIFACTS / "metrics_summary.md"


REQUIRED_KEYS = [
    "tri_engine_agreement",
    "qmc_vs_prng_equal_time",
    "pde_order",
    "ql_parity",
    "benchmarks",
    "wrds",
]


def run_snapshot() -> None:
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "generate_metrics_summary.py"),
        "--artifacts",
        str(ARTIFACTS),
        "--manifest",
        str(ARTIFACTS / "manifest.json"),
    ]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def assert_status_blocks(summary: Dict) -> None:
    metrics = summary.get("metrics")
    if not isinstance(metrics, dict):
        raise AssertionError("metrics key missing or not a dict")
    for key in REQUIRED_KEYS:
        if key not in metrics:
            raise AssertionError(f"missing metrics block: {key}")
        block = metrics[key]
        if "status" not in block:
            raise AssertionError(f"missing status in block {key}")
        if block["status"] not in {"ok", "missing", "parse_error"}:
            raise AssertionError(f"invalid status in block {key}: {block['status']}")


def test_snapshot_outputs_exist_and_parse() -> None:
    run_snapshot()
    if not JSON_OUT.exists():
        raise AssertionError("metrics_summary.json not created")
    if not MD_OUT.exists():
        raise AssertionError("metrics_summary.md not created")
    summary = load_json(JSON_OUT)
    assert_status_blocks(summary)


if __name__ == "__main__":
    test_snapshot_outputs_exist_and_parse()

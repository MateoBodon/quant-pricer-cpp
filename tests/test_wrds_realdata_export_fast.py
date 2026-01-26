#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _count_rows(path: Path) -> int:
    with path.open(newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def _assert_scalars(block: dict[str, Any], label: str) -> None:
    for key, value in block.items():
        if isinstance(value, (list, dict)):
            raise AssertionError(f"{label}.{key} is not scalar")
        if value is not None and not isinstance(value, (int, float)):
            raise AssertionError(f"{label}.{key} has non-numeric value: {value!r}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "wrds_realdata_metrics_export.py"
    wrds_root = repo_root / "docs" / "artifacts" / "wrds"
    manifest = repo_root / "docs" / "artifacts" / "manifest.json"

    if not script.exists():
        raise FileNotFoundError(script)
    if not wrds_root.exists():
        raise FileNotFoundError(wrds_root)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "metrics.json"
        out_md = tmp / "metrics.md"
        cmd = [
            sys.executable,
            str(script),
            "--wrds-root",
            str(wrds_root),
            "--use-sample",
            "--manifest",
            str(manifest),
            "--machine-label",
            "TEST_BOX",
            "--out",
            str(out_json),
            "--out-md",
            str(out_md),
        ]
        subprocess.check_call(cmd, cwd=repo_root)

        payload = json.loads(out_json.read_text())
        if payload.get("schema_version") != "wrds_realdata_metrics_export_v1":
            raise AssertionError("Unexpected schema_version")

        provenance = payload.get("provenance", {})
        for key in ["panel_id", "trade_date_range", "next_trade_date_range", "data_mode", "git_sha", "machine_label"]:
            if key not in provenance:
                raise AssertionError(f"Missing provenance.{key}")
        if provenance.get("machine_label") != "TEST_BOX":
            raise AssertionError("machine_label override not applied")
        if provenance.get("data_mode") != "sample":
            raise AssertionError("Expected data_mode 'sample' when --use-sample is set")
        for range_key in ["trade_date_range", "next_trade_date_range"]:
            dr = provenance.get(range_key)
            if not isinstance(dr, dict) or not dr.get("start") or not dr.get("end"):
                raise AssertionError(f"Invalid provenance.{range_key}")

        inputs = payload.get("inputs", {})
        for key, suffix in {
            "pricing_csv": "wrds_agg_pricing.csv",
            "oos_csv": "wrds_agg_oos.csv",
            "pnl_csv": "wrds_agg_pnl.csv",
            "comparison_csv": "wrds_bs_heston_comparison.csv",
        }.items():
            value = inputs.get(key, "")
            if not str(value).endswith(suffix):
                raise AssertionError(f"Expected inputs.{key} to end with {suffix}")

        metrics = payload.get("metrics", {})
        for section in ["pricing", "oos", "pnl", "comparison"]:
            if section not in metrics:
                raise AssertionError(f"Missing metrics.{section}")
            _assert_scalars(metrics[section], section)

        pricing_rows = _count_rows(wrds_root / "wrds_agg_pricing.csv")
        if metrics["pricing"].get("rows") != pricing_rows:
            raise AssertionError("pricing rows mismatch")

        export_text = json.dumps(payload, sort_keys=True)
        restricted_tokens = ["secid", "best_bid", "best_offer", "best_ask", "market_iv", "strike_price"]
        for token in restricted_tokens:
            if token in export_text:
                raise AssertionError(f"Restricted token found in export: {token}")

        if "WRDS real-data metrics export" not in out_md.read_text():
            raise AssertionError("Markdown output missing header")

        bad_root = tmp / "bad_wrds"
        bad_root.mkdir()
        for name in [
            "wrds_agg_pricing.csv",
            "wrds_agg_oos.csv",
            "wrds_agg_pnl.csv",
            "wrds_bs_heston_comparison.csv",
        ]:
            shutil.copy(wrds_root / name, bad_root / name)
        pricing_path = bad_root / "wrds_agg_pricing.csv"
        with pricing_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])
        fieldnames.append("secid")
        with pricing_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                row["secid"] = ""
                writer.writerow(row)
        bad_json = tmp / "bad_metrics.json"
        bad_md = tmp / "bad_metrics.md"
        bad_cmd = [
            sys.executable,
            str(script),
            "--wrds-root",
            str(bad_root),
            "--use-sample",
            "--manifest",
            str(manifest),
            "--out",
            str(bad_json),
            "--out-md",
            str(bad_md),
        ]
        try:
            subprocess.check_call(bad_cmd, cwd=repo_root)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("Exporter did not reject restricted columns")

        default_root = repo_root / "artifacts" / "_local" / "wrds_local"
        default_json = default_root / "metrics_export.json"
        default_md = default_root / "metrics_export.md"
        backups: dict[Path, bytes] = {}
        for path in (default_json, default_md):
            if path.exists():
                backups[path] = path.read_bytes()
        try:
            default_cmd = [
                sys.executable,
                str(script),
                "--wrds-root",
                str(wrds_root),
                "--use-sample",
                "--manifest",
                str(manifest),
                "--machine-label",
                "TEST_BOX",
            ]
            subprocess.check_call(default_cmd, cwd=repo_root)
            if not default_json.exists() or not default_md.exists():
                raise AssertionError("Default export outputs were not created")
            if "WRDS real-data metrics export" not in default_md.read_text():
                raise AssertionError("Default markdown output missing header")
        finally:
            for path, data in backups.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            if default_json not in backups and default_json.exists():
                default_json.unlink()
            if default_md not in backups and default_md.exists():
                default_md.unlink()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    reproduce_script = repo_root / "scripts" / "reproduce_wrds_local_metrics.sh"
    snippet_script = repo_root / "scripts" / "generate_wrds_resume_snippet.py"

    if not reproduce_script.exists():
        raise FileNotFoundError(reproduce_script)
    if not snippet_script.exists():
        raise FileNotFoundError(snippet_script)

    run_id = "wrds_local_ci_snippet"
    out_root = repo_root / "artifacts" / "_local" / "wrds_local" / run_id
    metrics_json = out_root / "metrics_export_sample.json"
    snippet_md = out_root / "resume_snippet_wrds_sample.md"

    env = os.environ.copy()
    env["WRDS_USE_SAMPLE"] = "1"
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"

    reproduce_cmd = [
        str(reproduce_script),
        "--dateset",
        "wrds_pipeline_dates_panel.yaml",
        "--run-id",
        run_id,
    ]
    reproduce_result = subprocess.run(
        reproduce_cmd,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if reproduce_result.returncode != 0:
        raise AssertionError(
            "Sample local-metrics reproduce script failed: "
            f"stdout={reproduce_result.stdout!r} stderr={reproduce_result.stderr!r}"
        )

    if not metrics_json.exists():
        raise AssertionError(f"Expected metrics export JSON at {metrics_json}")
    payload = json.loads(metrics_json.read_text())
    comparison = payload.get("metrics", {}).get("comparison", {})
    try:
        heston_iv_rmse = float(comparison["median_heston_iv_rmse_volpts"])
        bs_iv_rmse = float(comparison["median_bs_iv_rmse_volpts"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AssertionError("Sample export JSON missing valid Heston/BS comparison medians") from exc
    if bs_iv_rmse <= 0:
        raise AssertionError("Sample export JSON has non-positive BS IV RMSE; cannot validate percent improvement")
    improvement_pct = ((bs_iv_rmse - heston_iv_rmse) / bs_iv_rmse) * 100.0
    improvement_direction = "lower" if improvement_pct >= 0 else "higher"
    expected_improvement_text = f"~{abs(improvement_pct):.1f}% {improvement_direction}"

    snippet_cmd = [
        sys.executable,
        str(snippet_script),
        "--metrics-json",
        str(metrics_json),
    ]
    snippet_output = subprocess.check_output(snippet_cmd, cwd=repo_root, text=True).strip()
    if snippet_output != str(snippet_md.relative_to(repo_root)):
        raise AssertionError(
            "Unexpected snippet output path: "
            f"expected {snippet_md.relative_to(repo_root)!s}, got {snippet_output!r}"
        )

    if not snippet_md.exists():
        raise AssertionError(f"Expected snippet markdown at {snippet_md}")

    content = snippet_md.read_text()
    lower = content.lower()
    for token in ["/srv/data/wrds", ".parquet", ".csv"]:
        if token in lower:
            raise AssertionError(f"Snippet includes banned token {token!r}")

    if "# WRDS Resume Snippet (sample)" not in content:
        raise AssertionError("Snippet header missing or wrong mode")

    bullet_count = len([line for line in content.splitlines() if line.startswith("- ")])
    if bullet_count != 3:
        raise AssertionError(f"Expected 3 bullets, got {bullet_count}")

    if expected_improvement_text not in content:
        raise AssertionError(
            "Expected snippet to include computed Heston-vs-BS percent improvement: "
            f"{expected_improvement_text!r}"
        )

    if re.search(r"(?m)^([^,\n]*,){4,}[^,\n]*$", content):
        raise AssertionError("Snippet appears to contain row-level CSV-like data")

    if not str(snippet_md.resolve()).startswith(str(out_root.resolve())):
        raise AssertionError("Snippet was not written under artifacts/_local run output")


if __name__ == "__main__":
    main()

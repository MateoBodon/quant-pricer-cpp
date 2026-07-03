#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "reproduce_wrds_local_metrics.sh"
    manifest = repo_root / "docs" / "artifacts" / "manifest.json"

    if not script.exists():
        raise FileNotFoundError(script)
    if not manifest.exists():
        raise FileNotFoundError(manifest)

    before_hash = _sha256(manifest)

    run_id = "wrds_local_ci_smoke"
    out_root = repo_root / "artifacts" / "_local" / "wrds_local" / run_id
    out_json = out_root / "metrics_export_sample.json"
    out_md = out_root / "metrics_export_sample.md"

    env = os.environ.copy()
    env["WRDS_USE_SAMPLE"] = "1"
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"
    cmd = [str(script), "--dateset", "wrds_pipeline_dates_panel.yaml", "--run-id", run_id]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        raise AssertionError(
            "Script failed with exit code "
            f"{result.returncode}. stdout={stdout!r} stderr={stderr!r}"
        )

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("Expected script to print metrics markdown path")
    printed = Path(lines[-1]).resolve()
    if printed != out_md.resolve():
        raise AssertionError(f"Expected printed path {out_md.resolve()}, got {printed}")

    if not out_json.exists():
        raise AssertionError(f"Missing metrics export JSON at {out_json}")
    if not out_md.exists():
        raise AssertionError(f"Missing metrics export Markdown at {out_md}")

    after_hash = _sha256(manifest)
    if after_hash != before_hash:
        raise AssertionError("docs/artifacts/manifest.json changed during local run")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""FAST guard: gpt-bundle should fail on empty commit range."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_PREFIX = "_gpt_bundle_empty_diff_"
MIN_CONTENT = "self-test content for gpt-bundle\n"


def _find_ticket_id() -> str:
    ticket_path = REPO_ROOT / "docs" / "CODEX_SPRINT_TICKETS.md"
    if not ticket_path.exists():
        raise AssertionError("docs/CODEX_SPRINT_TICKETS.md missing")
    content = ticket_path.read_text(encoding="utf-8")
    match = re.search(r"ticket-\d+[a-z]?", content, re.IGNORECASE)
    if not match:
        raise AssertionError("no ticket id found in docs/CODEX_SPRINT_TICKETS.md")
    return match.group(0).lower()


def _write_run_log(run_name: str, ticket_id: str, head_sha: str) -> Path:
    run_dir = REPO_ROOT / "docs" / "agent_runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("PROMPT.md", "COMMANDS.md", "RESULTS.md", "TESTS.md"):
        (run_dir / name).write_text(MIN_CONTENT, encoding="utf-8")
    meta = {
        "run_name": run_name,
        "ticket_id": ticket_id,
        "started_at_utc": "1970-01-01T00:00:00Z",
        "finished_at_utc": "1970-01-01T00:00:01Z",
        "git_sha_before": head_sha,
        "git_sha_after": head_sha,
        "branch_name": "main",
        "host_os": "test",
        "compiler": "test",
        "python_version": sys.version.split()[0],
        "build_type": "Release",
        "dataset_id": "TEST",
        "config_hashes": {},
        "tools": {"runner": "fast-test"},
    }
    (run_dir / "META.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return run_dir


def main() -> None:
    ticket_id = _find_ticket_id()
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    run_name = f"{RUN_PREFIX}{uuid.uuid4().hex[:8]}"
    timestamp = f"TEST{uuid.uuid4().hex[:6].upper()}Z"
    output_path = (
        REPO_ROOT
        / "docs"
        / "gpt_bundles"
        / f"{timestamp}_{ticket_id}_{run_name}.zip"
    )
    run_dir = _write_run_log(run_name, ticket_id, head_sha)

    try:
        if output_path.exists():
            output_path.unlink()
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "gpt_bundle.py"),
            "--ticket",
            ticket_id,
            "--run-name",
            run_name,
            "--base-sha",
            head_sha,
            "--timestamp",
            timestamp,
        ]
        result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
        combined = (result.stdout + result.stderr).lower()
        if result.returncode == 0:
            raise AssertionError("gpt-bundle succeeded with an empty diff range")
        if "no commits in diff range" not in combined or "base_sha" not in combined:
            raise AssertionError(
                "expected empty-diff error message to mention commit range and BASE_SHA"
            )
    finally:
        if output_path.exists():
            output_path.unlink()
        if run_dir.exists():
            shutil.rmtree(run_dir)


if __name__ == "__main__":
    main()

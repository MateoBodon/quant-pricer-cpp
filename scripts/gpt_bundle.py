#!/usr/bin/env python3
"""Create the Prompt-3 GPT bundle zip."""
from __future__ import annotations

import argparse
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_git(args: List[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        return f"[error] {' '.join(args)}\n{exc.output}"


def _add_path(zf: zipfile.ZipFile, path: Path) -> None:
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                zf.write(item, str(item.relative_to(REPO_ROOT)))
    elif path.is_file():
        zf.write(path, str(path.relative_to(REPO_ROOT)))


def _required_items(run_name: str) -> List[Tuple[str, Path]]:
    return [
        ("AGENTS.md", REPO_ROOT / "AGENTS.md"),
        ("docs/PLAN_OF_RECORD.md", REPO_ROOT / "docs" / "PLAN_OF_RECORD.md"),
        ("docs/DOCS_AND_LOGGING_SYSTEM.md", REPO_ROOT / "docs" / "DOCS_AND_LOGGING_SYSTEM.md"),
        ("docs/CODEX_SPRINT_TICKETS.md", REPO_ROOT / "docs" / "CODEX_SPRINT_TICKETS.md"),
        ("PROGRESS.md", REPO_ROOT / "PROGRESS.md"),
        ("project_state/CURRENT_RESULTS.md", REPO_ROOT / "project_state" / "CURRENT_RESULTS.md"),
        ("project_state/KNOWN_ISSUES.md", REPO_ROOT / "project_state" / "KNOWN_ISSUES.md"),
        ("project_state/CONFIG_REFERENCE.md", REPO_ROOT / "project_state" / "CONFIG_REFERENCE.md"),
        (
            f"docs/agent_runs/{run_name}",
            REPO_ROOT / "docs" / "agent_runs" / run_name,
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the Prompt-3 GPT bundle zip.")
    parser.add_argument("--ticket", required=True, help="Ticket id (e.g., ticket-01)")
    parser.add_argument("--run-name", required=True, help="Run name under docs/agent_runs/")
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Optional UTC timestamp for the bundle filename (e.g., 20251221T185600Z)",
    )
    args = parser.parse_args()

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = REPO_ROOT / "docs" / "gpt_bundles"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}_{args.ticket}_{args.run_name}.zip"

    required = _required_items(args.run_name)
    missing: List[str] = []

    diff_text = _run_git(["git", "diff", "--patch"])
    cached_text = _run_git(["git", "diff", "--cached", "--patch"])
    if diff_text.strip() and cached_text.strip():
        diff_payload = (
            "### git diff --patch (working tree)\n"
            + diff_text
            + "\n\n### git diff --cached --patch (staged)\n"
            + cached_text
        )
    else:
        diff_payload = diff_text if diff_text.strip() else cached_text
    if not diff_payload.strip():
        diff_payload = "No local diff\n"

    last_commit = _run_git(["git", "log", "-1", "--pretty=fuller"])

    with zipfile.ZipFile(
        output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
        for label, path in required:
            if not path.exists():
                missing.append(label)
                continue
            _add_path(zf, path)

        zf.writestr("DIFF.patch", diff_payload)
        zf.writestr("LAST_COMMIT.txt", last_commit)

    print(f"[gpt-bundle] wrote {output_path}")
    if missing:
        print("[gpt-bundle] missing items:")
        for item in missing:
            print(f"  - {item}")


if __name__ == "__main__":
    main()

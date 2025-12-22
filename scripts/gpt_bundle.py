#!/usr/bin/env python3
"""Create the Prompt-3 GPT bundle zip."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "AGENTS.md",
    "docs/PLAN_OF_RECORD.md",
    "docs/DOCS_AND_LOGGING_SYSTEM.md",
    "docs/CODEX_SPRINT_TICKETS.md",
    "PROGRESS.md",
    "project_state/CURRENT_RESULTS.md",
    "project_state/KNOWN_ISSUES.md",
    "project_state/CONFIG_REFERENCE.md",
    "docs/agent_runs/{run_name}/PROMPT.md",
    "docs/agent_runs/{run_name}/COMMANDS.md",
    "docs/agent_runs/{run_name}/RESULTS.md",
    "docs/agent_runs/{run_name}/TESTS.md",
    "docs/agent_runs/{run_name}/META.json",
)


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


def _render_required_paths(run_name: str) -> List[str]:
    return [path.format(run_name=run_name) for path in REQUIRED_PATHS]


def _required_items(run_name: str) -> List[Tuple[str, Path]]:
    items: List[Tuple[str, Path]] = []
    for rel_path in _render_required_paths(run_name):
        items.append((rel_path, REPO_ROOT / rel_path))
    return items


def _ticket_present(ticket_path: Path, ticket_id: str) -> bool:
    if not ticket_path.exists():
        return False
    try:
        content = ticket_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return ticket_id.lower() in content.lower()


def _verify_zip(zip_path: Path, required_paths: Iterable[str]) -> List[str]:
    if not zip_path.exists():
        return [str(zip_path)]
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
    missing = [path for path in required_paths if path not in names]
    return missing


def _find_ticket_id(ticket_path: Path) -> str | None:
    if not ticket_path.exists():
        return None
    try:
        content = ticket_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"ticket-\d+[a-z]?", content, re.IGNORECASE)
    if not match:
        return None
    return match.group(0).lower()


def _run_self_test() -> int:
    ticket_path = REPO_ROOT / "docs" / "CODEX_SPRINT_TICKETS.md"
    valid_ticket = _find_ticket_id(ticket_path)
    if not valid_ticket:
        print("[gpt-bundle] self-test failed: no ticket id found in docs/CODEX_SPRINT_TICKETS.md")
        return 2

    temp_run_name = f"_gpt_bundle_selftest_{uuid.uuid4().hex[:8]}"
    run_dir = REPO_ROOT / "docs" / "agent_runs" / temp_run_name
    run_log_paths = [
        REPO_ROOT / path
        for path in _render_required_paths(temp_run_name)
        if path.startswith("docs/agent_runs/")
    ]

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        for path in run_log_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("self-test\n", encoding="utf-8")

        missing_run = f"{temp_run_name}_missing"
        missing_cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--ticket",
            valid_ticket,
            "--run-name",
            missing_run,
        ]
        missing_result = subprocess.run(
            missing_cmd, cwd=REPO_ROOT, text=True, capture_output=True
        )
        print("[gpt-bundle][self-test] missing-file exit code:", missing_result.returncode)
        if missing_result.stdout:
            print(missing_result.stdout.rstrip())
        if missing_result.stderr:
            print(missing_result.stderr.rstrip())
        if missing_result.returncode == 0 or "missing required items" not in (
            missing_result.stdout + missing_result.stderr
        ).lower():
            print("[gpt-bundle][self-test] missing-file case did not fail as expected.")
            return 1

        missing_ticket = "ticket-does-not-exist"
        ticket_cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--ticket",
            missing_ticket,
            "--run-name",
            temp_run_name,
        ]
        ticket_result = subprocess.run(
            ticket_cmd, cwd=REPO_ROOT, text=True, capture_output=True
        )
        print("[gpt-bundle][self-test] missing-ticket exit code:", ticket_result.returncode)
        if ticket_result.stdout:
            print(ticket_result.stdout.rstrip())
        if ticket_result.stderr:
            print(ticket_result.stderr.rstrip())
        if ticket_result.returncode == 0 or "ticket id not found" not in (
            ticket_result.stdout + ticket_result.stderr
        ).lower():
            print("[gpt-bundle][self-test] missing-ticket case did not fail as expected.")
            return 1
    finally:
        if run_dir.exists():
            shutil.rmtree(run_dir)

    print("[gpt-bundle] self-test passed")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the Prompt-3 GPT bundle zip.")
    parser.add_argument("--ticket", help="Ticket id (e.g., ticket-01)")
    parser.add_argument("--run-name", help="Run name under docs/agent_runs/")
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Optional UTC timestamp for the bundle filename (e.g., 20251221T185600Z)",
    )
    parser.add_argument(
        "--verify",
        metavar="ZIP",
        help="Verify that an existing bundle contains the required files for this ticket/run.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run negative tests to prove missing-file and missing-ticket failures.",
    )
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_run_self_test())

    if not args.ticket or not args.run_name:
        parser.error("--ticket and --run-name are required unless --self-test is used")

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = REPO_ROOT / "docs" / "gpt_bundles"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}_{args.ticket}_{args.run_name}.zip"

    required = _required_items(args.run_name)
    required_labels = [label for label, _ in required]
    missing = [label for label, path in required if not path.exists()]
    ticket_path = REPO_ROOT / "docs" / "CODEX_SPRINT_TICKETS.md"
    ticket_ok = _ticket_present(ticket_path, args.ticket)

    if args.verify:
        required_zip = required_labels + ["DIFF.patch", "LAST_COMMIT.txt"]
        missing_in_zip = _verify_zip(Path(args.verify), required_zip)
        if missing_in_zip:
            print("[gpt-bundle] bundle verification failed; missing entries:")
            for item in missing_in_zip:
                print(f"  - {item}")
            sys.exit(1)
        print(f"[gpt-bundle] bundle verification passed: {args.verify}")
        return

    if missing or not ticket_ok:
        if missing:
            print("[gpt-bundle] missing required items:")
            for item in missing:
                print(f"  - {item}")
        if not ticket_ok:
            print(
                f"[gpt-bundle] ticket id not found in docs/CODEX_SPRINT_TICKETS.md: {args.ticket}"
            )
        sys.exit(1)

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
        for _, path in required:
            _add_path(zf, path)

        zf.writestr("DIFF.patch", diff_payload)
        zf.writestr("LAST_COMMIT.txt", last_commit)

    print(f"[gpt-bundle] wrote {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Create the Prompt-3 GPT bundle zip."""
from __future__ import annotations

import argparse
import json
import os
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
try:
    MIN_RUNLOG_BYTES = int(os.getenv("GPT_BUNDLE_MIN_RUNLOG_BYTES", "20"))
except ValueError:
    MIN_RUNLOG_BYTES = 20


def _run_git(args: List[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        return f"[error] {' '.join(args)}\n{exc.output}"


def _try_git(args: List[str]) -> str | None:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _check_git(args: List[str]) -> bool:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    return result.returncode == 0


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


def _run_log_issues(required: List[Tuple[str, Path]], run_name: str) -> List[str]:
    issues: List[str] = []
    run_prefix = f"docs/agent_runs/{run_name}/"
    min_bytes = max(1, MIN_RUNLOG_BYTES)
    for label, path in required:
        if not label.startswith(run_prefix):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            issues.append(f"{label} (unreadable)")
            continue
        if size < min_bytes:
            issues.append(f"{label} ({size} bytes < {min_bytes})")
    return issues


def _meta_issues(meta_path: Path) -> List[str]:
    issues: List[str] = []
    try:
        with meta_path.open("r", encoding="utf-8") as fh:
            meta = json.load(fh)
    except OSError as exc:
        issues.append(f"META.json unreadable: {exc}")
        return issues
    except json.JSONDecodeError as exc:
        issues.append(f"META.json invalid JSON: {exc}")
        return issues

    sha = meta.get("git_sha_after")
    if not isinstance(sha, str) or not sha.strip():
        issues.append("META.json missing git_sha_after")
        return issues
    sha = sha.strip()
    if not _check_git(["git", "cat-file", "-e", f"{sha}^{{commit}}"]):
        issues.append(f"META.json git_sha_after not found in repo: {sha}")
        return issues
    if not _check_git(["git", "merge-base", "--is-ancestor", sha, "HEAD"]):
        issues.append(f"META.json git_sha_after not in HEAD history: {sha}")
    return issues


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


def _resolve_base_sha(ticket_id: str, explicit_base: str | None) -> Tuple[str | None, str | None]:
    base = explicit_base or os.getenv("BASE_SHA")
    if base:
        return base, "explicit"

    for ref in ("main", "origin/main"):
        if _try_git(["git", "rev-parse", "--verify", ref]):
            merge_base = _try_git(["git", "merge-base", "HEAD", ref])
            if merge_base:
                return merge_base, f"merge-base:{ref}"

    ticket_match = _try_git(
        ["git", "log", "--reverse", "--format=%H", "--grep", re.escape(ticket_id)]
    )
    if ticket_match:
        commit = ticket_match.splitlines()[0].strip()
        parent = _try_git(["git", "rev-parse", f"{commit}^"])
        return parent or commit, f"ticket-grep:{commit}"

    return None, None


def _build_diff_payload(base_sha: str | None) -> Tuple[str, str]:
    sections: List[str] = []
    commit_log = ""
    if base_sha:
        base_diff = _run_git(["git", "diff", "--patch", f"{base_sha}..HEAD"])
        if base_diff.strip():
            sections.append(f"### git diff --patch {base_sha}..HEAD\n{base_diff}")
        commit_log = _run_git(["git", "log", "--oneline", f"{base_sha}..HEAD"])

    work_diff = _run_git(["git", "diff", "--patch"])
    if work_diff.strip():
        sections.append("### git diff --patch (working tree)\n" + work_diff)

    cached_diff = _run_git(["git", "diff", "--cached", "--patch"])
    if cached_diff.strip():
        sections.append("### git diff --cached --patch (staged)\n" + cached_diff)

    diff_payload = "\n\n".join(sections) if sections else "No diff\n"
    return diff_payload, commit_log


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
        "--base-sha",
        help="Optional base commit for DIFF.patch (defaults to BASE_SHA env or merge-base).",
    )
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
    run_log_issues = _run_log_issues(required, args.run_name)
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

    if missing or run_log_issues or not ticket_ok:
        if missing:
            print("[gpt-bundle] missing required items:")
            for item in missing:
                print(f"  - {item}")
        if run_log_issues:
            print("[gpt-bundle] run log files missing content:")
            for item in run_log_issues:
                print(f"  - {item}")
        if not ticket_ok:
            print(
                f"[gpt-bundle] ticket id not found in docs/CODEX_SPRINT_TICKETS.md: {args.ticket}"
            )
        sys.exit(1)

    meta_issues = _meta_issues(REPO_ROOT / f"docs/agent_runs/{args.run_name}/META.json")
    if meta_issues:
        print("[gpt-bundle] run log META.json invalid:")
        for item in meta_issues:
            print(f"  - {item}")
        sys.exit(1)

    base_sha, base_source = _resolve_base_sha(args.ticket, args.base_sha)
    if base_sha and not _try_git(["git", "rev-parse", "--verify", base_sha]):
        print(f"[gpt-bundle] base SHA not found: {base_sha}")
        sys.exit(1)
    if base_sha:
        print(f"[gpt-bundle] using base SHA {base_sha} ({base_source})")

    diff_payload, commit_log = _build_diff_payload(base_sha)

    last_commit = _run_git(["git", "log", "-1", "--pretty=fuller"])
    commit_payload = ""
    if base_sha:
        commit_payload = f"Base SHA: {base_sha}\nBase source: {base_source}\n\n"
        commit_payload += commit_log.strip() + ("\n" if commit_log.strip() else "")
        if not commit_log.strip():
            commit_payload += "No commits in range\n"
    else:
        commit_payload = "Base SHA: (not set)\n"

    with zipfile.ZipFile(
        output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
        for _, path in required:
            _add_path(zf, path)

        zf.writestr("DIFF.patch", diff_payload)
        zf.writestr("COMMITS.txt", commit_payload)
        zf.writestr("LAST_COMMIT.txt", last_commit)

    print(f"[gpt-bundle] wrote {output_path}")


if __name__ == "__main__":
    main()

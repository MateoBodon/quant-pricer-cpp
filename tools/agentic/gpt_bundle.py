#!/usr/bin/env python3
"""
gpt_bundle.py

Creates a zip bundle intended to be uploaded to GPT for review.

Outputs:
  artifacts/_local/gpt_bundles/gpt_bundle_<timestamp>[_<ticket>].zip

The bundle includes:
- docs/_generated/repo_snapshot.md (auto-generated / refreshed)
- git status, log, base..HEAD diff evidence
- ticket file (if present)
- run-log files (if --run-name is provided)
- selected small changed files (best-effort)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


def run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="replace")


def git_root(start: Path) -> Optional[Path]:
    code, out = run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    return Path(out.strip())


RUNLOG_FILES = ("PROMPT.md", "COMMANDS.md", "RESULTS.md", "TESTS.md", "META.json")


def ensure_repo_snapshot(repo: Path, refresh: bool = True) -> Optional[Path]:
    snap = repo / "docs" / "_generated" / "repo_snapshot.md"
    tool = repo / "tools" / "agentic" / "repo_snapshot.py"
    if refresh and tool.exists():
        code, out = run([sys.executable, str(tool)], cwd=repo)
        if code == 0:
            p = Path(out.strip().splitlines()[-1]).resolve()
            if p.exists():
                return p
    if snap.exists():
        return snap
    return None


def _append_unique_paths(target: list[str], raw: str) -> None:
    for line in raw.splitlines():
        rel = line.strip()
        if rel and rel not in target:
            target.append(rel)


def _ref_exists(repo: Path, ref: str) -> bool:
    code, _ = run(["git", "-C", str(repo), "rev-parse", "--verify", ref])
    return code == 0


def resolve_base_sha(repo: Path, explicit_base: Optional[str], base_ref: str) -> Tuple[Optional[str], Optional[str]]:
    candidate = (explicit_base or os.getenv("BASE_SHA") or "").strip()
    if candidate:
        code, out = run(["git", "-C", str(repo), "rev-parse", "--verify", candidate])
        if code == 0:
            return out.strip(), "explicit"
        return None, f"invalid:{candidate}"

    for ref in (base_ref, "main", "origin/main"):
        if not ref:
            continue
        if not _ref_exists(repo, ref):
            continue
        code, out = run(["git", "-C", str(repo), "merge-base", "HEAD", ref])
        if code == 0 and out.strip():
            return out.strip(), f"merge-base:{ref}"
    return None, None


def list_changed_files(repo: Path, base_sha: Optional[str]) -> list[str]:
    changed: list[str] = []

    if base_sha:
        _, out = run(["git", "-C", str(repo), "diff", "--name-only", f"{base_sha}..HEAD"])
        _append_unique_paths(changed, out)

    _, out = run(["git", "-C", str(repo), "diff", "--name-only"])
    _append_unique_paths(changed, out)

    _, out2 = run(["git", "-C", str(repo), "diff", "--cached", "--name-only"])
    _append_unique_paths(changed, out2)

    _, out3 = run(["git", "-C", str(repo), "status", "--porcelain"])
    for line in out3.splitlines():
        if not line.startswith("?? "):
            continue
        rel = line[3:].strip()
        if rel and rel not in changed:
            changed.append(rel)
    return changed


def add_file_if_small(
    z: zipfile.ZipFile,
    repo: Path,
    rel_path: str,
    max_bytes: int = 120_000,
    source_override: Optional[Path] = None,
) -> None:
    p = source_override or (repo / rel_path)
    if not p.exists() or not p.is_file():
        return
    try:
        if p.stat().st_size > max_bytes:
            return
        arcname = rel_path if source_override else str(p.relative_to(repo))
        z.write(p, arcname=arcname)
    except Exception:
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true", help="Create zip bundle (default behavior).")
    ap.add_argument("--ticket", type=str, default=None, help="Ticket id to include (optional).")
    ap.add_argument("--run-name", type=str, default=None, help="Run log name under docs/agent_runs/ to include.")
    ap.add_argument("--out", type=str, default=None, help="Output zip path (optional).")
    ap.add_argument(
        "--base-sha",
        type=str,
        default=None,
        help="Optional base commit for commit-range diff evidence (defaults to merge-base with --base-ref).",
    )
    ap.add_argument(
        "--base-ref",
        type=str,
        default="main",
        help="Reference branch/ref for merge-base when --base-sha is not provided (default: main).",
    )
    ap.add_argument(
        "--allow-empty-diff",
        action="store_true",
        help="Allow writing a bundle when no commit-range/working/staged diff exists.",
    )
    ap.add_argument("--include-files", action="store_true", help="Include small changed files in addition to diffs.")
    ap.add_argument(
        "--no-stash",
        action="store_true",
        help="Disable automatic stashing when the repo is dirty.",
    )
    ap.add_argument(
        "--self-check",
        action="store_true",
        help="Print the bundle output path and dirty-tree strategy, then exit.",
    )
    args = ap.parse_args()

    start = Path.cwd()
    repo = git_root(start) or start

    def git_status_porcelain() -> str:
        code, out = run(["git", "-C", str(repo), "status", "--porcelain"])
        return out if code == 0 else ""

    def stash_push(message: str) -> Optional[str]:
        code, out = run(["git", "-C", str(repo), "stash", "push", "-u", "-m", message])
        if code != 0:
            print("[gpt-bundle] stash failed:")
            print(out.rstrip())
            return None
        _, ref = run(["git", "-C", str(repo), "stash", "list", "-n", "1", "--format=%H"])
        return ref.strip() or None

    def stash_apply(ref: str) -> Tuple[bool, str]:
        code, out = run(["git", "-C", str(repo), "stash", "apply", "--index", ref])
        return code == 0, out

    def stash_drop(ref: str) -> None:
        run(["git", "-C", str(repo), "stash", "drop", ref])

    status_before = git_status_porcelain()
    dirty = bool(status_before.strip())

    bundles_dir = repo / "artifacts" / "_local" / "gpt_bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ticket = (args.ticket or "").strip()
    suffix = f"_{ticket}" if ticket else ""
    out_zip = Path(args.out) if args.out else (bundles_dir / f"gpt_bundle_{ts}{suffix}.zip")

    if args.self_check:
        print(f"[gpt-bundle] dirty: {'yes' if dirty else 'no'}")
        print(f"[gpt-bundle] stash: {'no' if args.no_stash else ('yes' if dirty else 'no')}")
        print(f"[gpt-bundle] output: {out_zip}")
        return 0

    # Refresh snapshot on every run to avoid stale review context.
    snap = ensure_repo_snapshot(repo, refresh=True)

    base_sha, base_source = resolve_base_sha(repo, args.base_sha, args.base_ref)
    if base_source and base_source.startswith("invalid:"):
        print(f"[gpt-bundle] base SHA not found: {base_source.split(':', 1)[1]}")
        return 1
    if base_sha:
        print(f"[gpt-bundle] using base SHA {base_sha} ({base_source})")

    # Collect git info (capture before any stash).
    _, status = run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = run(["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"])
    _, diff_work = run(["git", "-C", str(repo), "diff", "--patch"])
    _, diff_cached = run(["git", "-C", str(repo), "diff", "--cached", "--patch"])
    _, diff_range = run(
        ["git", "-C", str(repo), "diff", "--patch", f"{base_sha}..HEAD"]
    ) if base_sha else (0, "")
    _, diff_stat = run(
        ["git", "-C", str(repo), "diff", "--stat", f"{base_sha}..HEAD"]
    ) if base_sha else run(["git", "-C", str(repo), "diff", "--stat"])
    _, commit_log = run(
        ["git", "-C", str(repo), "log", "--oneline", f"{base_sha}..HEAD"]
    ) if base_sha else (0, "")
    changed = list_changed_files(repo, base_sha)

    diff_sections: list[str] = []
    if base_sha:
        if diff_range.strip():
            diff_sections.append(f"### git diff --patch {base_sha}..HEAD\n{diff_range}")
    if diff_work.strip():
        diff_sections.append("### git diff --patch (working tree)\n" + diff_work)
    if diff_cached.strip():
        diff_sections.append("### git diff --cached --patch (staged)\n" + diff_cached)

    if not diff_sections and not args.allow_empty_diff:
        print(
            "[gpt-bundle] No diff evidence found in base..HEAD, working tree, or staged index. "
            "Pass --allow-empty-diff to override."
        )
        return 1

    diff_payload = "\n\n".join(diff_sections) if diff_sections else "No diff\n"
    commit_payload = []
    if base_sha:
        commit_payload.append(f"Base SHA: {base_sha}")
        commit_payload.append(f"Base source: {base_source}")
        commit_payload.append("")
        commit_payload.append(commit_log.strip() or "No commits in range")
    else:
        commit_payload.append("Base SHA: (not set)")
    commits_txt = "\n".join(commit_payload).rstrip() + "\n"

    ticket_content = None
    if ticket:
        tf = repo / "docs" / "tickets" / f"{ticket}.md"
        if tf.exists():
            try:
                ticket_content = tf.read_text(encoding="utf-8")
            except OSError:
                ticket_content = None

    snap_content = None
    if snap and snap.exists():
        try:
            snap_content = snap.read_text(encoding="utf-8")
        except OSError:
            snap_content = None

    runlog_files: list[Path] = []
    if args.run_name:
        runlog_dir = repo / "docs" / "agent_runs" / args.run_name
        for name in RUNLOG_FILES:
            candidate = runlog_dir / name
            if candidate.exists() and candidate.is_file():
                runlog_files.append(candidate)
            else:
                print(f"[gpt-bundle] warning: missing run log file {candidate}")

    stash_used = False
    stash_ref: Optional[str] = None
    temp_dir = None
    changed_copies: Dict[str, Path] = {}

    readme = f"""GPT Bundle

Generated: {ts}Z
Repo: {repo}
Ticket: {ticket or "(none)"}
Run name: {args.run_name or "(none)"}
Base SHA: {base_sha or "(not set)"}
Base source: {base_source or "(not set)"}

Contents:
- docs/_generated/repo_snapshot.md (if available)
- git_status.txt
- git_log.txt
- DIFF.patch (base..HEAD + working tree + staged)
- git_diff.patch (compat: commit-range diff when available)
- git_diff_cached.patch (staged)
- git_diff_stat.txt
- changed_files.txt
- COMMITS.txt
- docs/agent_runs/<run_name>/* (if --run-name was provided)
- ticket file (if present)
- small changed files (optional)
"""

    try:
        if dirty and not args.no_stash:
            if args.include_files and changed:
                temp_dir = Path(tempfile.mkdtemp(prefix="gpt_bundle_"))
                for rel in changed:
                    src = repo / rel
                    if not src.exists() or not src.is_file():
                        continue
                    try:
                        dest = temp_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(src.read_bytes())
                        changed_copies[rel] = dest
                    except OSError:
                        continue

            stash_ref = stash_push(f"temp: gpt_bundle {ticket or ts}")
            if not stash_ref:
                return 1
            stash_used = True
            if git_status_porcelain().strip():
                print("[gpt-bundle] stash did not clean the working tree.")
                return 1

        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("README.txt", readme)
            z.writestr("git_status.txt", status)
            z.writestr("git_log.txt", log)
            z.writestr("DIFF.patch", diff_payload)
            z.writestr("COMMITS.txt", commits_txt)
            z.writestr("git_diff.patch", diff_range if diff_range.strip() else diff_work)
            z.writestr("git_diff_cached.patch", diff_cached)
            z.writestr("git_diff_stat.txt", diff_stat)
            z.writestr("changed_files.txt", "\n".join(changed) + ("\n" if changed else ""))

            if snap_content is not None and snap:
                z.writestr(str(snap.relative_to(repo)), snap_content)
            elif snap and snap.exists():
                z.write(snap, arcname=str(snap.relative_to(repo)))

            if ticket and ticket_content is not None:
                z.writestr(f"docs/tickets/{ticket}.md", ticket_content)
            elif ticket:
                tf = repo / "docs" / "tickets" / f"{ticket}.md"
                if tf.exists():
                    z.write(tf, arcname=str(tf.relative_to(repo)))

            for runlog_path in runlog_files:
                z.write(runlog_path, arcname=str(runlog_path.relative_to(repo)))

            if args.include_files:
                for rel in changed:
                    add_file_if_small(
                        z,
                        repo,
                        rel,
                        source_override=changed_copies.get(rel),
                    )
    finally:
        if stash_used and stash_ref:
            applied, out = stash_apply(stash_ref)
            if not applied:
                print("[gpt-bundle] stash apply failed; resolve manually:")
                print(out.rstrip())
                print(f"[gpt-bundle] stash ref preserved: {stash_ref}")
                return 1
            status_after = git_status_porcelain()
            if status_after != status_before:
                print("[gpt-bundle] stash restore mismatch; resolve before dropping stash.")
                print(f"[gpt-bundle] stash ref preserved: {stash_ref}")
                return 1
            stash_drop(stash_ref)

        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[gpt-bundle] dirty: {'yes' if dirty else 'no'}")
    print(f"[gpt-bundle] stash: {'yes' if stash_used else 'no'}")
    print(f"[gpt-bundle] wrote {out_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

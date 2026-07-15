#!/usr/bin/env python3
"""
gpt_bundle.py

Creates a zip bundle intended to be uploaded to GPT for review.

Outputs:
  artifacts/_local/gpt_bundles/gpt_bundle_<timestamp>[_<ticket>].zip

The bundle includes:
- docs/_generated/repo_snapshot.md (auto-generated)
- git status, log, diffs
- ticket file (if present)
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
        out = subprocess.check_output(
            cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.STDOUT
        )
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="replace")


def git_root(start: Path) -> Optional[Path]:
    code, out = run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    return Path(out.strip())


def ensure_repo_snapshot(repo: Path) -> Optional[Path]:
    snap = repo / "docs" / "_generated" / "repo_snapshot.md"
    if snap.exists():
        return snap
    tool = repo / "tools" / "agentic" / "repo_snapshot.py"
    if tool.exists():
        code, out = run([sys.executable, str(tool)], cwd=repo)
        if code == 0:
            p = Path(out.strip().splitlines()[-1])
            if p.exists():
                return p
    return None


def list_changed_files(repo: Path) -> list[str]:
    # Prefer git diff names for working tree
    _, out = run(["git", "-C", str(repo), "diff", "--name-only"])
    changed = [l.strip() for l in out.splitlines() if l.strip()]
    # Include staged
    _, out2 = run(["git", "-C", str(repo), "diff", "--cached", "--name-only"])
    for l in out2.splitlines():
        l = l.strip()
        if l and l not in changed:
            changed.append(l)
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
    ap.add_argument(
        "--zip", action="store_true", help="Create zip bundle (default behavior)."
    )
    ap.add_argument(
        "--ticket", type=str, default=None, help="Ticket id to include (optional)."
    )
    ap.add_argument("--out", type=str, default=None, help="Output zip path (optional).")
    ap.add_argument(
        "--include-files",
        action="store_true",
        help="Include small changed files in addition to diffs.",
    )
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
        _, ref = run(
            ["git", "-C", str(repo), "stash", "list", "-n", "1", "--format=%H"]
        )
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
    out_zip = (
        Path(args.out) if args.out else (bundles_dir / f"gpt_bundle_{ts}{suffix}.zip")
    )

    if args.self_check:
        print(f"[gpt-bundle] dirty: {'yes' if dirty else 'no'}")
        print(
            f"[gpt-bundle] stash: {'no' if args.no_stash else ('yes' if dirty else 'no')}"
        )
        print(f"[gpt-bundle] output: {out_zip}")
        return 0

    # Ensure snapshot exists
    snap = ensure_repo_snapshot(repo)

    # Collect git info (capture before any stash)
    _, status = run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = run(["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"])
    _, diff = run(["git", "-C", str(repo), "diff"])
    _, diff_cached = run(["git", "-C", str(repo), "diff", "--cached"])
    _, diff_stat = run(["git", "-C", str(repo), "diff", "--stat"])
    changed = list_changed_files(repo)

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

    stash_used = False
    stash_ref: Optional[str] = None
    temp_dir = None
    changed_copies: Dict[str, Path] = {}

    readme = f"""GPT Bundle

Generated: {ts}Z
Repo: {repo}
Ticket: {ticket or "(none)"}

Contents:
- docs/_generated/repo_snapshot.md (if available)
- git_status.txt
- git_log.txt
- git_diff.patch (working tree)
- git_diff_cached.patch (staged)
- git_diff_stat.txt
- changed_files.txt
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
            z.writestr("git_diff.patch", diff)
            z.writestr("git_diff_cached.patch", diff_cached)
            z.writestr("git_diff_stat.txt", diff_stat)
            z.writestr(
                "changed_files.txt", "\n".join(changed) + ("\n" if changed else "")
            )

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
                print(
                    "[gpt-bundle] stash restore mismatch; resolve before dropping stash."
                )
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

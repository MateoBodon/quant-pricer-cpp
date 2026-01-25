#!/usr/bin/env python3
"""
gpt_bundle.py

Creates a zip bundle intended to be uploaded to GPT for review.

Outputs:
  docs/_bundles/gpt_bundle_<timestamp>[_<ticket>].zip

The bundle includes:
- docs/_generated/repo_snapshot.md (auto-generated)
- git status, log, diffs
- ticket file (if present)
- selected small changed files (best-effort)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


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


def add_file_if_small(z: zipfile.ZipFile, repo: Path, rel_path: str, max_bytes: int = 120_000) -> None:
    p = repo / rel_path
    if not p.exists() or not p.is_file():
        return
    try:
        if p.stat().st_size > max_bytes:
            return
        z.write(p, arcname=str(p.relative_to(repo)))
    except Exception:
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true", help="Create zip bundle (default behavior).")
    ap.add_argument("--ticket", type=str, default=None, help="Ticket id to include (optional).")
    ap.add_argument("--out", type=str, default=None, help="Output zip path (optional).")
    ap.add_argument("--include-files", action="store_true", help="Include small changed files in addition to diffs.")
    args = ap.parse_args()

    start = Path.cwd()
    repo = git_root(start) or start

    # Ensure snapshot exists
    snap = ensure_repo_snapshot(repo)

    # Collect git info
    _, status = run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = run(["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"])
    _, diff = run(["git", "-C", str(repo), "diff"])
    _, diff_cached = run(["git", "-C", str(repo), "diff", "--cached"])
    _, diff_stat = run(["git", "-C", str(repo), "diff", "--stat"])
    changed = list_changed_files(repo)

    bundles_dir = repo / "docs" / "_bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ticket = (args.ticket or "").strip()
    suffix = f"_{ticket}" if ticket else ""
    out_zip = Path(args.out) if args.out else (bundles_dir / f"gpt_bundle_{ts}{suffix}.zip")

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

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", readme)
        z.writestr("git_status.txt", status)
        z.writestr("git_log.txt", log)
        z.writestr("git_diff.patch", diff)
        z.writestr("git_diff_cached.patch", diff_cached)
        z.writestr("git_diff_stat.txt", diff_stat)
        z.writestr("changed_files.txt", "\n".join(changed) + ("\n" if changed else ""))

        if snap and snap.exists():
            z.write(snap, arcname=str(snap.relative_to(repo)))

        # Ticket file
        if ticket:
            tf = repo / "docs" / "tickets" / f"{ticket}.md"
            if tf.exists():
                z.write(tf, arcname=str(tf.relative_to(repo)))

        if args.include_files:
            for rel in changed:
                add_file_if_small(z, repo, rel)

    print(str(out_zip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

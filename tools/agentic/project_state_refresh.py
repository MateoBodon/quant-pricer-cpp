#!/usr/bin/env python3
"""
project_state_refresh.py

Creates/updates deterministic repo metadata under:
  project_state/_generated/

Optionally creates a zip bundle for GPT recenter:
  docs/_bundles/project_state_<timestamp>.zip

This script does NOT attempt to "understand" the repo. It creates the
stable raw materials that an AI agent can summarize accurately.
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


DEFAULT_PROJECT_STATE_FILES = {
    "README.md": """# project_state

This folder is the repo’s **high-signal memory** for AI planning.

Keep these documents:
- accurate
- short
- practical

A fresh GPT session should be able to answer:
- What is this repo?
- How do I run/test it?
- What are the modules?
- What is broken?
- What should happen next?

Generated artifacts live in `_generated/`.
""",
    "ARCHITECTURE.md": """# Architecture

- High-level modules:
- Data flow:
- Key invariants:
""",
    "RUNBOOK.md": """# Runbook

## Setup
- (commands)

## Build
- (commands)

## Test
- (commands)

## Debug
- (tips)
""",
    "KNOWN_ISSUES.md": """# Known issues

- (bullets)
""",
    "BACKLOG.md": """# Backlog

Ranked, short.
- (bullets)
""",
}


def ensure_templates(project_state_dir: Path) -> None:
    project_state_dir.mkdir(parents=True, exist_ok=True)
    for name, content in DEFAULT_PROJECT_STATE_FILES.items():
        p = project_state_dir / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")


def write_generated(repo: Path, project_state_dir: Path) -> None:
    gen = project_state_dir / "_generated"
    gen.mkdir(parents=True, exist_ok=True)

    # git info
    _, head = run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    _, branch = run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])
    _, status = run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = run(["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"])
    _, diff = run(["git", "-C", str(repo), "diff"])
    _, diff_cached = run(["git", "-C", str(repo), "diff", "--cached"])
    _, ls_files = run(["git", "-C", str(repo), "ls-files"])

    (gen / "git_head.txt").write_text(head, encoding="utf-8")
    (gen / "git_branch.txt").write_text(branch, encoding="utf-8")
    (gen / "git_status.txt").write_text(status, encoding="utf-8")
    (gen / "git_log.txt").write_text(log, encoding="utf-8")
    (gen / "git_diff.patch").write_text(diff, encoding="utf-8")
    (gen / "git_diff_cached.patch").write_text(diff_cached, encoding="utf-8")
    (gen / "git_ls_files.txt").write_text(ls_files, encoding="utf-8")

    # simple dependency hints
    dep = []
    for fname in ["Cargo.toml", "package.json", "pyproject.toml", "requirements.txt", "CMakeLists.txt", "Makefile"]:
        if (repo / fname).exists():
            dep.append(fname)
    (gen / "dependency_hints.txt").write_text("\n".join(dep) + ("\n" if dep else ""), encoding="utf-8")


def zip_project_state(repo: Path, project_state_dir: Path, out_zip: Path) -> Path:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # include project_state/*
        for p in sorted(project_state_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(repo)
            z.write(p, arcname=str(rel))

        # include key root docs if present
        for p in [repo/"PROJECT.md", repo/"PROGRESS.md", repo/"AGENTS.md", repo/"README.md"]:
            if p.exists() and p.is_file():
                z.write(p, arcname=str(p.relative_to(repo)))

        # include key docs if present
        for p in [repo/"docs"/"RUNBOOK.md", repo/"docs"/"DECISIONS.md", repo/"docs"/"PLAN_OF_RECORD.md"]:
            if p.exists() and p.is_file():
                z.write(p, arcname=str(p.relative_to(repo)))

    return out_zip


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true", help="Create project_state zip in docs/_bundles/")
    ap.add_argument("--out", type=str, default=None, help="Zip output path (optional)")
    args = ap.parse_args()

    start = Path.cwd()
    repo = git_root(start) or start
    project_state_dir = repo / "project_state"

    ensure_templates(project_state_dir)
    write_generated(repo, project_state_dir)

    print(f"[ok] Updated {project_state_dir}/_generated")

    if args.zip:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_zip = Path(args.out) if args.out else (repo / "docs" / "_bundles" / f"project_state_{ts}.zip")
        out = zip_project_state(repo, project_state_dir, out_zip)
        print(str(out))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

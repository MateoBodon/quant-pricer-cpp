#!/usr/bin/env python3
"""
Create a deterministic, lightweight repo snapshot for GPT review.

Outputs:
  docs/_generated/repo_snapshot.md

This is intentionally non-AI: it is cheap, fast, and stable.
"""
from __future__ import annotations

import argparse
import collections
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple


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


def git_ls_files(repo: Path) -> list[str]:
    code, out = run(["git", "-C", str(repo), "ls-files"])
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def guess_language_counts(paths: Iterable[str]) -> dict[str, int]:
    exts = collections.Counter()
    for p in paths:
        ext = Path(p).suffix.lower() or "<noext>"
        exts[ext] += 1
    return dict(exts.most_common(25))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, default=None, help="Output path (default: docs/_generated/repo_snapshot.md)")
    args = ap.parse_args()

    start = Path.cwd()
    repo = git_root(start) or start

    tracked = git_ls_files(repo)
    lang = guess_language_counts(tracked)

    # Basic git info
    _, head = run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    _, branch = run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])
    _, status = run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = run(["git", "-C", str(repo), "log", "-n", "20", "--oneline", "--decorate"])

    # Tree (depth-limited)
    tree_lines = []
    # Prefer "git ls-files" (stable ordering)
    for p in tracked[:1200]:
        tree_lines.append(p)
    if len(tracked) > 1200:
        tree_lines.append(f"... ({len(tracked) - 1200} more tracked files)")

    out_path = Path(args.out) if args.out else (repo / "docs" / "_generated" / "repo_snapshot.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    md = f"""# Repo Snapshot

Generated: **{now}**  
Repo root: `{repo}`

## Git
- Branch: `{branch.strip() or "?"}`
- HEAD: `{head.strip() or "?"}`

### Status (porcelain)
```text
{status.strip()}
```

### Recent commits
```text
{log.strip()}
```

## File stats (top extensions)
```json
{lang}
```

## Tracked file list (truncated)
```text
{os.linesep.join(tree_lines)}
```

## Suggested next commands
- `git status`
- `git diff`
- `python3 tools/agentic/gpt_bundle.py --zip --ticket <TICKET_ID>`
"""

    out_path.write_text(md, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

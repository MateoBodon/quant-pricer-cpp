#!/usr/bin/env python3
"""tools/agentic/runlog_init.py

Create a new docs/agent_runs/<RUN_NAME>/ folder with a standard set of files.

This is intentionally *dumb* and deterministic: it does not call any LLM.
It exists so both humans and agents can start runs with consistent logging.

Typical usage:
  python3 tools/agentic/runlog_init.py --ticket "QP-TKT-010c" --summary "Normalize tracking policy"
  python3 tools/agentic/runlog_init.py --run-name "20260126_204606_ticket-10c_tracking-policy-wrds-local" --ticket "ticket-10c" --summary "..."

Outputs:
  - prints the created run directory path to stdout
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple


def _utc_now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "run"


def _run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="replace")


def _git_root(start: Path) -> Path:
    code, out = _run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if code == 0:
        return Path(out.strip())
    return start


def _git_head(repo: Path) -> str:
    code, out = _run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    return out.strip() if code == 0 else ""


def _git_branch(repo: Path) -> str:
    code, out = _run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip() if code == 0 else ""


@dataclass(frozen=True)
class RunMeta:
    run_name: str
    ticket: str
    summary: str
    created_at_utc: str
    repo_root: str
    git_branch: str
    git_head: str
    hostname: str
    user: str
    python: str


TEMPLATE_PROMPT = """# Prompt

Ticket: **{ticket}**
Run: **{run_name}**
Summary: {summary}

## Goal
- [ ] (One sentence) What must be true at the end of this run?

## Constraints
- [ ] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [ ] No secrets in repo or logs
- [ ] Tests run (or explicitly marked N/A)

## Plan
1.
2.
3.

## Files to touch (expected)
- (list)

## Definition of Done
- [ ] Acceptance criteria met
- [ ] PROGRESS.md updated
- [ ] Run log filled (RESULTS/TESTS)
"""


TEMPLATE_COMMANDS = """# Commands

Log commands that materially change state or produce results.

- (time) command
  - outcome / notes
"""


TEMPLATE_RESULTS = """# Results

## Summary
- (What changed?)
- (Where are the outputs?)

## Key outputs
- Path:
- Path:

## Notes
- Risks / follow-ups:
"""


TEMPLATE_TESTS = """# Tests

- [ ] Command:
  - Result:

If tests were skipped, explain why and what to run later.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", required=True, help="Ticket id or filename-safe label (e.g., QP-TKT-010c or ticket-10c)")
    ap.add_argument("--summary", default="", help="One-line purpose for this run")
    ap.add_argument("--run-name", default=None, help="Explicit run folder name. If omitted, one is generated.")
    ap.add_argument("--root", default=None, help="Repo root (defaults to git root from cwd)")
    args = ap.parse_args()

    start = Path.cwd()
    repo = Path(args.root).resolve() if args.root else _git_root(start)

    stamp = _utc_now_stamp()
    ticket_slug = _slug(args.ticket)
    run_name = args.run_name or f"{stamp}_ticket-{ticket_slug}"

    run_dir = repo / "docs" / "agent_runs" / run_name
    if run_dir.exists():
        if not run_dir.is_dir():
            raise SystemExit(f"Run path exists and is not a directory: {run_dir}")
        print(str(run_dir))
        return 0
    run_dir.mkdir(parents=True, exist_ok=False)

    meta = RunMeta(
        run_name=run_name,
        ticket=args.ticket,
        summary=args.summary,
        created_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_root=str(repo),
        git_branch=_git_branch(repo),
        git_head=_git_head(repo),
        hostname=socket.gethostname(),
        user=os.getenv("USER") or os.getenv("USERNAME") or "",
        python=sys.version.replace("\n", " "),
    )

    # Write files
    (run_dir / "PROMPT.md").write_text(
        TEMPLATE_PROMPT.format(ticket=args.ticket, run_name=run_name, summary=args.summary or "(none)"),
        encoding="utf-8",
    )
    (run_dir / "COMMANDS.md").write_text(TEMPLATE_COMMANDS, encoding="utf-8")
    (run_dir / "RESULTS.md").write_text(TEMPLATE_RESULTS, encoding="utf-8")
    (run_dir / "TESTS.md").write_text(TEMPLATE_TESTS, encoding="utf-8")
    (run_dir / "META.json").write_text(json.dumps(asdict(meta), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""tools/agentic/ticket_new.py

Create a new ticket file under docs/tickets/ from a standard template.

This is optional; many teams prefer authoring tickets via GPT Prompt 2.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "ticket"


TEMPLATE = """# {title}

## Goal
{goal}

## Context
- (links / files)

## Constraints
- Follow TRACKING_POLICY.md (no surprise top-level dirs)
- Create a run log under docs/agent_runs/<RUN_NAME>/
- Bulky outputs go to artifacts/_local/ or reports/_runs/

## Plan
1.
2.
3.

## Acceptance criteria
- [ ]

## Test plan
- [ ]

## Artifacts / Outputs
- (expected paths)

## Notes / Risks
- (anything that could go wrong)
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="Ticket id (e.g., 10c or QP-TKT-010c)")
    ap.add_argument("--slug", required=True, help="Short slug for filename")
    ap.add_argument("--title", default=None, help="Ticket title (defaults to derived from slug)")
    ap.add_argument("--goal", default="(one sentence)", help="One-line goal")
    ap.add_argument("--repo", default=".", help="Path inside repo (default: .)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    tickets_dir = repo / "docs" / "tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)

    fname = f"ticket-{_slug(args.id)}_{_slug(args.slug)}.md"
    path = tickets_dir / fname
    if path.exists():
        raise SystemExit(f"Ticket already exists: {path}")

    title = args.title or args.slug.replace("-", " ").strip().title()
    content = TEMPLATE.format(title=title, goal=args.goal)

    path.write_text(content, encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

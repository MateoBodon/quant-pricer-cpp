#!/usr/bin/env python3
"""tools/agentic/validate_runlog.py

Validate that a run log folder exists and contains the minimum required files.

This is intentionally lightweight (no repo-specific heuristics).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

REQUIRED = ["PROMPT.md", "COMMANDS.md", "RESULTS.md", "TESTS.md", "META.json"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", default=None, help="Run folder name under docs/agent_runs/")
    ap.add_argument("--path", default=None, help="Explicit path to the run folder")
    ap.add_argument("--repo", default=".", help="Path inside repo (default: .)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if args.path:
        run_dir = Path(args.path).resolve()
    elif args.run_name:
        run_dir = repo / "docs" / "agent_runs" / args.run_name
    else:
        raise SystemExit("Provide --run-name or --path")

    ok = True
    missing: List[str] = []
    for f in REQUIRED:
        if not (run_dir / f).exists():
            ok = False
            missing.append(f)

    if not run_dir.exists():
        print(f"FAIL: run dir missing: {run_dir}")
        return 2

    if missing:
        print(f"FAIL: missing files in {run_dir}:")
        for m in missing:
            print(f"  - {m}")
        return 2

    # Basic META.json sanity
    try:
        meta = json.loads((run_dir / "META.json").read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise ValueError("META.json not a JSON object")
    except Exception as e:
        print(f"FAIL: META.json invalid: {e}")
        ok = False

    if ok:
        print(f"OK: {run_dir}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

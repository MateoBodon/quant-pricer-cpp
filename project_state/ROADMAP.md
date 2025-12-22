---
generated_at: 2025-12-22T19:13:19Z
git_sha: 5265c6de1a7e13f4bfc8708f188986cee30b18ed
branch: feature/ticket-00_project_state_refresh
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - c++ --version
  - cmake --version
  - uname -a
  - rg --files
  - rg --files -g '*.py'
  - rg --files tests
  - rg -n "argparse|click|typer" scripts wrds_pipeline python tests tools
  - python3 tools/project_state_generate.py
---

# Roadmap (condensed)

Source: `ROADMAP (1).md`.

## Phase 0 — Housekeeping & baseline
- Document current state and workflows (AGENTS/ROADMAP/coverage baselines).
- Run full test suite and refresh artifacts via `scripts/reproduce_all.sh`.

## Phase 1 — Numerical robustness & tests
- Improve Heston QE bias and document convergence.
- Increase branch coverage in barrier/risk/CLI paths; add focused tests.

## Phase 2 — WRDS OptionMetrics flagship
- Harden WRDS pipeline and sampling panel documentation.
- Expand BS vs Heston comparisons and summary plots.
- Add opt-in MARKET tests for live WRDS runs.

## Phase 3 — Developer experience & documentation
- Tighten README/Results narratives and coverage reporting.
- Improve automation for reproducible bundles and audits.

## Notes
- The roadmap file contains detailed checklists and references; see `ROADMAP (1).md` for specifics.

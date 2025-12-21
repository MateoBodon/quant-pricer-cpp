---
generated_at: 2025-12-20T21:11:15Z
git_sha: 36c52c1d72dbcaacd674729ea9ab4719b3fd6408
branch: master
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - rg --files
  - rg --files -g '*.py'
  - python3 tools/project_state_generate.py
  - uname -a
  - cmake --version
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
- Add highlight bullets to README with links to artifacts.
- Tighten Results/WRDS narratives and coverage reporting.

## Notes
- The roadmap file contains detailed checklists and references; see `ROADMAP (1).md` for specifics.

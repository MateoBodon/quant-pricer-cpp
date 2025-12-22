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

# Research Notes

## Core docs
- `docs/Design.md` — design overview, engine comparisons, and numerical method notes.
- `docs/Greeks.md` — derivations and estimator notes for pathwise/LR Greeks.
- `docs/Validation.md` / `docs/ValidationHighlights.md` — validation summaries tied to artifact outputs.
- `docs/Results.md` — curated results page backing the GitHub Pages site.
- `docs/WRDS_Results.md` — WRDS pipeline narrative, metrics, and sample-vs-live cautions.
- `docs/ValidationHighlights.md` — quick pointers to key diagnostics and artifacts.

## Notable research themes (from repo docs)
- Cross-validating analytic/MC/PDE engines for sanity checks.
- Variance reduction + QMC (Sobol + Brownian bridge) for MC convergence.
- PDE convergence diagnostics (order ≈ -2 slope) and grid stretching.
- Heston analytic vs QE Monte Carlo comparisons (bias tracked in roadmap).
- WRDS OptionMetrics pipeline with vega×quote-weighted calibration and OOS diagnostics.

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

# Research Notes

## Core docs
- `docs/Design.md` — design overview, engine comparisons, and numerical method notes.
- `docs/Greeks.md` — derivations and estimator notes for pathwise/LR Greeks.
- `docs/Validation.md` / `docs/ValidationHighlights.md` — validation summaries tied to artifact outputs.
- `docs/Results.md` — curated results page backing the GitHub Pages site.
- `docs/WRDS_Results.md` — WRDS pipeline narrative, metrics, and sample-vs-live cautions.

## Notable research themes (from repo docs)
- Cross-validating analytic/MC/PDE engines for sanity checks.
- Variance reduction + QMC (Sobol + Brownian bridge) for MC convergence.
- PDE convergence diagnostics (order ≈ -2 slope) and grid stretching.
- Heston analytic vs QE Monte Carlo comparisons (bias still tracked in roadmap).
- WRDS OptionMetrics pipeline with vega×quote-weighted calibration and OOS diagnostics.

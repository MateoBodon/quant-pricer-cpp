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

# Changelog (summary)

Source: `CHANGELOG.md`.

## Unreleased
- Andersen QE variance paths and deterministic RNG for MC/Heston; CLI/pybind CI for MC Greeks.

## v0.3.2
- WRDS multi-date panel artifacts (vega-weighted RMSE/MAE, OOS, Δ-hedged PnL) and deterministic sample bundle.
- Benchmarks refreshed; documentation + manifest updates.
- QuantLib parity script + published CSV/PNG.
- Docs + release wiring updates; version bumps.

## v0.3.1
- CLI smoke test added; coverage HTML committed for GH Pages.
- Validation pack packaging script and release workflow.
- Version bumps for project + Python package.

## v0.3.0
- Pybind bindings expanded to Heston/PDE/MC stats.
- Heston characteristic function + implied vol APIs.
- cibuildwheel builds and consumer CMake example.

## v0.2.0
- QMC (Sobol + Brownian bridge), barrier analytics/MC/PDE, American PSOR/LSMC, PDE improvements.
- Artifact pipeline and CLI enhancements.

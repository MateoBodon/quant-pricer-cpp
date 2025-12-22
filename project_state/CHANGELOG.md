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

# Changelog (summary)

Source: `CHANGELOG.md`.

## Unreleased
- Heston QE variance paths + deterministic RNG; CLI/pybind MC Greeks confidence intervals.
- Repro pipeline hard-fails if required artifacts are missing; validation pack emitted after reproduction.
- Data-policy guard requiring `# SYNTHETIC_DATA` markers; regenerated synthetic WRDS sample data.
- Added `requirements-dev.txt` (matplotlib/QuantLib) for FAST tests/artifacts.
- WRDS parquet cache support + bulk cache builder script.
- Explicit-only WRDS local mode and local manifest inclusion in validation bundle.

- Docs: project_state refresh and regenerated indices.
## v0.3.2
- WRDS multi-date panel artifacts with vega-weighted RMSE/MAE, OOS bps, Δ-hedged PnL.
- Benchmarks refreshed with plots + manifest integration.
- QuantLib parity script and published CSV/PNG.
- Docs + release wiring updates; version bump.

## v0.3.1
- CLI smoke test and coverage HTML published to Pages.
- Validation pack packaging script + release workflow.
- Version bump for project + Python package.

## v0.3.0
- Pybind bindings expanded (Heston CF/implied vol, PDE + MC stats).
- CIBW wheels + consumer CMake example.

## v0.2.0
- QMC Sobol + Brownian bridge, barrier analytics/MC/PDE, American PSOR/LSMC, PDE improvements.
- Artifact pipeline and CLI enhancements; reproducible demo assets.

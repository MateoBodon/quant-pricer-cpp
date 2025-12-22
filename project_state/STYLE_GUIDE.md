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

# Style Guide

## C++
- Standard: C++20 (see `CMakeLists.txt`).
- Formatting and linting: clang-format / clang-tidy as configured in the repo (per `AGENTS.md`).
- Namespaces: use existing `quant::` namespaces (`quant::bs`, `quant::mc`, `quant::pde`, `quant::heston`, etc.).
- New modules: headers under `include/quant/`, implementations under `src/`, tests under `tests/`.

## Python
- Keep scripts small, single-purpose; prefer argparse for CLI entrypoints.
- When producing artifacts, prefer `docs/artifacts/` for reproducible outputs and update `docs/artifacts/manifest.json` via `scripts/manifest_utils.py`.
- For sample data under `wrds_pipeline/sample_data/`, include `# SYNTHETIC_DATA` headers.

## Repo conventions
- Follow run logging protocol in `docs/DOCS_AND_LOGGING_SYSTEM.md`.
- Do not commit raw WRDS data; only aggregated CSV/PNG under `docs/artifacts/wrds/` (sample-only).
- Tests should be labeled FAST/SLOW/MARKET and wired into CMake.

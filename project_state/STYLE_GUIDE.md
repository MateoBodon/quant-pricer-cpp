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

# Style Guide

## C++
- Standard: C++20 (see `CMakeLists.txt`).
- Formatting and linting: clang-format / clang-tidy as configured in the repo (per `AGENTS.md`).
- Namespaces: use existing `quant::` namespaces (`quant::bs`, `quant::mc`, `quant::pde`, `quant::heston`, etc.).
- New modules: headers under `include/quant/`, implementations under `src/`, tests under `tests/`.

## Python
- Keep scripts small, single-purpose; prefer argparse or direct function entrypoints.
- When producing artifacts, write to `docs/artifacts/` and update `docs/artifacts/manifest.json` via `scripts/manifest_utils.py`.

## Repo conventions
- Prefer existing scripts/patterns (see `scripts/reproduce_all.sh`, `wrds_pipeline/`).
- Do not commit raw WRDS data; only aggregated CSV/PNG under `docs/artifacts/wrds/`.
- Tests should be labeled FAST/SLOW/MARKET and wired into CMake.

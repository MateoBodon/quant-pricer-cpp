---
generated_at: 2025-12-21T20:30:38Z
git_sha: 30002fe1a2fd69644b54a36237b8d820da8743f0
branch: feature/ticket-06-wrds-local-guardrails
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

# Config Reference

## Build configuration
- `CMakeLists.txt`
  - `QUANT_ENABLE_OPENMP` (default ON)
  - `QUANT_ENABLE_SANITIZERS` (default OFF)
  - `QUANT_ENABLE_CLANG_TIDY` (default OFF)
  - `QUANT_ENABLE_PYBIND` (default OFF)
- `cmake/quant-pricer-config.cmake.in` (install package config).
- `conanfile.py`, `vcpkg.json` (dependency managers).

## Python packaging
- `pyproject.toml`
  - scikit-build-core backend, `QUANT_ENABLE_PYBIND=ON`, build dir `build-py`.
- `setup.cfg` (legacy metadata).

## WRDS pipeline configuration
- `wrds_pipeline_dates_panel.yaml` — trade-date panel and labels.
- Environment variables (see `AGENTS.md`, `wrds_pipeline/tests/test_wrds_pipeline.py`):
  - `WRDS_ENABLED=1` to enable live IvyDB pulls.
  - `WRDS_USERNAME`, `WRDS_PASSWORD` for credentials.
  - `WRDS_USE_SAMPLE=1` for deterministic sample bundle.
  - `WRDS_CACHE_ROOT` to override output location (used by MARKET tests).
  - `WRDS_LOCAL_ROOT` to explicitly enable local OptionMetrics parquet mode.
- `wrds_pipeline_dates_panel.yaml` optional keys:
  - `wrds_local_root` — explicit local OptionMetrics root (used only if set).

## Artifact reproduction configuration
- `scripts/reproduce_all.sh` environment overrides:
  - `BUILD_DIR`, `BUILD_TYPE`, `REPRO_FAST`, `SKIP_SLOW`, `SKIP_WRDS`, `BENCH_MIN_TIME`.
  - `WRDS_USE_SAMPLE`, `WRDS_SYMBOL`, `WRDS_TRADE_DATE`, `WRDS_DATESET`.
- `scripts/package_validation.py` — bundles `docs/artifacts` into a validation zip.

## CLI configuration
- `quant_cli` flags documented in `src/main.cpp` (per-engine argument parsing).

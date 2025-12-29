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

# Config Reference

## Build configuration
- `CMakeLists.txt`
  - `QUANT_ENABLE_OPENMP` (default ON)
  - `QUANT_ENABLE_SANITIZERS` (default OFF)
  - `QUANT_ENABLE_CLANG_TIDY` (default OFF)
  - `QUANT_ENABLE_PYBIND` (default OFF)
  - `CMAKE_CXX_STANDARD=20`
- `cmake/quant-pricer-config.cmake.in` (install package config).
- `conanfile.py`, `vcpkg.json` (dependency managers).

## Python packaging
- `pyproject.toml`
  - scikit-build-core backend, `QUANT_ENABLE_PYBIND=ON`, build dir `build-py`.
- `setup.cfg` (legacy metadata).
- `requirements-artifacts.txt`, `requirements-dev.txt` (artifact/test deps; includes matplotlib, scipy, QuantLib).

## WRDS pipeline configuration
- `wrds_pipeline_dates_panel.yaml` — canonical multi-date panel (must include `panel_id`; optional `wrds_local_root`).
- Override the dateset path:
  - CLI: `python -m wrds_pipeline.pipeline --dateset <path>`
  - `scripts/reproduce_all.sh`: `WRDS_DATESET=<path>` (defaults to `wrds_pipeline_dates_panel.yaml`).
- `panel_id` is required; legacy `dataset_id` fields hard-error to avoid protocol drift.
- Provenance (manifest):
  - `runs.wrds_dateset[].panel_id`
  - `runs.wrds_dateset[].dateset_inputs` (config hash + size)
  - `runs.wrds_dateset[].use_sample` + `runs.wrds_dateset[].data_mode` (sample/local/live)
  - `runs.wrds_dateset[].trade_date_range` + `runs.wrds_dateset[].next_trade_date_range`
- Environment variables (see `AGENTS.md`, `wrds_pipeline/tests/test_wrds_pipeline.py`):
  - `WRDS_ENABLED=1` to enable live IvyDB pulls.
  - `WRDS_USERNAME`, `WRDS_PASSWORD` for credentials.
  - `WRDS_USE_SAMPLE=1` for deterministic sample bundle.
  - `WRDS_CACHE_ROOT` to override cache location.
  - `WRDS_LOCAL_ROOT` to explicitly enable local OptionMetrics parquet mode.
  - `WRDS_SAMPLE_PATH` to override the WRDS sample CSV path (used by FAST poison tests).
  - `WRDS_SYMBOL`, `WRDS_TRADE_DATE`, `WRDS_DATESET` for targeted runs.

## Artifact reproduction configuration
- `scripts/reproduce_all.sh` environment overrides:
  - `BUILD_DIR`, `BUILD_TYPE`, `REPRO_FAST`, `SKIP_SLOW`, `SKIP_WRDS`, `BENCH_MIN_TIME`.
  - `WRDS_USE_SAMPLE`, `WRDS_SYMBOL`, `WRDS_TRADE_DATE`, `WRDS_DATESET`.
- `scripts/package_validation.py` — bundles `docs/artifacts` into a validation zip.
- `scripts/gpt_bundle.py` — bundles project state + run logs into GPT-friendly zips.

## Data-policy guard
- `scripts/check_data_policy.py` scans tracked CSVs for restricted patterns and requires `# SYNTHETIC_DATA` markers under `wrds_pipeline/sample_data/`.

## CLI configuration
- `quant_cli` flags are defined in `src/main.cpp` (per-engine argument parsing and JSON output).

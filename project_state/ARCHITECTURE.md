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

# Architecture

## System overview
- **C++20 core library** (`include/quant/`, `src/`): pricing engines for Black–Scholes analytics, Monte Carlo, PDE, barriers, American, exotics, Heston, risk, multi-asset.
- **CLI executable** (`src/main.cpp` → `quant_cli`): command-line pricing front-end for multiple engines with JSON output option.
- **Python bindings** (`python/pybind_module.cpp` + `pyproject.toml`): `pyquant_pricer` via pybind11/scikit-build.
- **Artifacts + validation** (`scripts/`, `docs/artifacts/`): reproducible figures/CSVs and manifest metadata.
- **WRDS pipeline** (`wrds_pipeline/`): IvyDB/OptionMetrics ingestion, calibration, OOS and Δ-hedge aggregates.

## Core C++ library layout
- Public API headers live in `include/quant/` (namespaces such as `quant::bs`, `quant::mc`, `quant::pde`, `quant::heston`).
- Implementations live in `src/` (one .cpp per engine or component).
- QMC utilities are under `include/quant/qmc/` and `src/qmc/`.
- RNG abstractions and term structures are shared across engines (`include/quant/rng.hpp`, `include/quant/term_structures.hpp`).

## CLI architecture
- `quant_cli` composes the same headers the library exposes (`src/main.cpp`).
- Engines are routed by the first CLI argument: `bs`, `iv`, `mc`, `barrier`, `pde`, `american`, `digital`, `asian`, `heston`, `risk`.
- Optional JSON output is supported for scripting and test harnesses.

## Python bindings
- `python/pybind_module.cpp` binds a subset of the core API (BS, MC, PDE, American, barrier, Heston, risk).
- Build is driven by CMake and scikit-build (`pyproject.toml` with `QUANT_ENABLE_PYBIND=ON`).
- Example usage lives in `python/examples/quickstart.py`.

## Data/artifact architecture
- Artifact generation scripts are under `scripts/` and write to `docs/artifacts/`.
- `scripts/reproduce_all.sh` orchestrates build + tests + artifact refresh and updates `docs/artifacts/manifest.json` via `scripts/manifest_utils.py`.
- Metrics snapshot summaries are derived by `scripts/generate_metrics_summary.py` (outputs `docs/artifacts/metrics_summary.md/json`).

## WRDS pipeline architecture
- Entry point: `python -m wrds_pipeline.pipeline` (`wrds_pipeline/pipeline.py`).
- Pipeline stages: surface ingest → calibration (Heston/BS) → OOS pricing → Δ-hedged PnL → aggregated CSV/PNG outputs.
- Configuration for multi-date runs is in `wrds_pipeline_dates_panel.yaml`.
- MARKET tests wrap the pipeline (`wrds_pipeline/tests/test_wrds_pipeline.py`).

## Key repository layout
- `include/quant/` — public C++ headers (API surface).
- `src/` — C++ implementations + CLI (`src/main.cpp`).
- `python/` — pybind module + examples.
- `wrds_pipeline/` — WRDS pipeline package.
- `scripts/` — experiment and artifact generation scripts.
- `benchmarks/` — Google Benchmark targets.
- `tests/` — C++ unit tests and Python FAST tests.
- `docs/` — docs, results, and artifacts (`docs/artifacts/`).

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

# Architecture

## System overview
- **C++20 core library** (`include/quant/`, `src/`): Black–Scholes analytics, Monte Carlo (QMC + VR), PDE, American, barrier, exotic, Heston, risk, and multi-asset engines.
- **CLI executable** (`src/main.cpp` → `quant_cli`): command-line front-end for core engines with optional JSON output.
- **Python bindings** (`python/pybind_module.cpp`, `pyproject.toml`): `pyquant_pricer` via pybind11/scikit-build-core.
- **Artifacts + validation** (`scripts/`, `docs/artifacts/`): reproducible CSV/PNG evidence, metrics summary, validation bundle.
- **WRDS pipeline** (`wrds_pipeline/`): IvyDB/OptionMetrics ingest, calibration, OOS, and Δ-hedge diagnostics (sample-only by default).
- **Run logging + bundles** (`docs/agent_runs/`, `scripts/gpt_bundle.py`, `docs/gpt_bundles/`): auditable runs and GPT bundles.

## Core C++ library layout
- Public API headers live in `include/quant/` (namespaces: `quant::bs`, `quant::mc`, `quant::pde`, `quant::american`, `quant::heston`, `quant::risk`).
- Implementations live in `src/` (one `.cpp` per engine/component).
- QMC utilities are under `include/quant/qmc/` and `src/qmc/`.
- Shared utilities: RNGs (`include/quant/rng.hpp`), term structures (`include/quant/term_structures.hpp`), math/stats helpers.

## CLI architecture
- `quant_cli` routes by the first argument: `bs`, `iv`, `mc`, `barrier`, `pde`, `american`, `digital`, `asian`, `heston`, `risk`.
- Each engine builds parameter structs and calls the corresponding C++ API, emitting text or JSON.

## Python bindings
- `pyquant_pricer` exposes BS analytics/Greeks, MC pricing + Greeks, PDE pricing, American (binomial/PSOR/LSMC), barrier BS/MC/PDE, Heston analytic + MC, and risk utilities.
- Build is driven by scikit-build-core (`pyproject.toml`), with `QUANT_ENABLE_PYBIND=ON`.

## Data/artifact architecture
- Artifact scripts in `scripts/` emit CSV/PNG outputs under `docs/artifacts/` during reproducible runs.
- `scripts/manifest_utils.py` maintains `docs/artifacts/manifest.json` (git + system metadata).
- `scripts/generate_metrics_summary.py` produces `docs/artifacts/metrics_summary.md/json` (single source of truth for status).
- Data-policy guard: `scripts/check_data_policy.py` enforces restricted-column rules and `# SYNTHETIC_DATA` markers for sample CSVs.

## WRDS pipeline architecture
- Entry point: `python -m wrds_pipeline.pipeline` (`wrds_pipeline/pipeline.py`).
- Pipeline stages: surface ingest (`ingest_sppx_surface`) → calibration (`calibrate_heston` + `calibrate_bs`) → OOS pricing (`oos_pricing`) → Δ-hedged PnL (`delta_hedge_pnl`) → aggregation/plots (`pipeline.py`).
- Canonical multi-date configuration lives in `wrds_pipeline_dates_panel.yaml` (with an explicit `panel_id` logged into provenance).

## Key repository layout
- `include/quant/` — public C++ headers (API surface).
- `src/` — C++ implementations + CLI (`src/main.cpp`).
- `python/` — pybind module + examples.
- `wrds_pipeline/` — WRDS pipeline package.
- `scripts/` — artifact generation, validation, and tooling scripts.
- `benchmarks/` — Google Benchmark targets.
- `tests/` — C++ unit tests and Python FAST tests.
- `docs/` — docs, results, and artifacts (`docs/artifacts/`).

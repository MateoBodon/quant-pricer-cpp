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

# Dependency Graph

## Python internal imports (AST-derived)
Derived from `project_state/_generated/import_graph.json` (internal modules only).

- `scripts.build_wrds_cache` → `wrds_pipeline`, `wrds_pipeline.ingest_sppx_surface`
- `wrds_pipeline.calibrate_bs` → `wrds_pipeline.bs_utils`, `wrds_pipeline.calibrate_heston`
- `wrds_pipeline.calibrate_heston` → `wrds_pipeline.bs_utils`
- `wrds_pipeline.delta_hedge_pnl` → `wrds_pipeline.bs_utils`
- `wrds_pipeline.ingest_sppx_surface` → `wrds_pipeline.bs_utils`
- `wrds_pipeline.oos_pricing` → `wrds_pipeline.calibrate_heston`
- `wrds_pipeline.pipeline` → `wrds_pipeline.calibrate_bs`, `wrds_pipeline.calibrate_heston`, `wrds_pipeline.compare_bs_heston`, `wrds_pipeline.delta_hedge_pnl`, `wrds_pipeline.ingest_sppx_surface`, `wrds_pipeline.oos_pricing`

## C++ dependency notes (high-level)
- `src/*.cpp` implement the APIs declared in `include/quant/*.hpp`.
- External dependencies are pulled either as submodules (`external/googletest`, `external/benchmark`, `external/pcg`) or via FetchContent in `CMakeLists.txt`.
- `src/main.cpp` (CLI) depends on most core headers (`quant::bs`, `quant::mc`, `quant::pde`, `quant::american`, `quant::heston`, `quant::risk`).
- QMC components (`src/qmc/*`, `include/quant/qmc/*`) are used by Monte Carlo engines.

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

# Dependency Graph

## Python internal imports (AST-derived)
Derived from `project_state/_generated/import_graph.json` (internal modules only).

- `wrds_pipeline.calibrate_bs` → wrds_pipeline.bs_utils, wrds_pipeline.calibrate_heston
- `wrds_pipeline.calibrate_heston` → wrds_pipeline.bs_utils
- `wrds_pipeline.delta_hedge_pnl` → wrds_pipeline.bs_utils
- `wrds_pipeline.ingest_sppx_surface` → wrds_pipeline.bs_utils
- `wrds_pipeline.oos_pricing` → wrds_pipeline.calibrate_heston
- `wrds_pipeline.pipeline` → wrds_pipeline.calibrate_bs, wrds_pipeline.calibrate_heston, wrds_pipeline.compare_bs_heston, wrds_pipeline.delta_hedge_pnl, wrds_pipeline.ingest_sppx_surface, wrds_pipeline.oos_pricing

## C++ dependency notes (high-level)
- `src/*.cpp` implement the APIs declared in `include/quant/*.hpp`.
- External dependencies are pulled either as submodules (`external/googletest`, `external/benchmark`) or via FetchContent (see `CMakeLists.txt`).
- `src/main.cpp` (CLI) depends on most core headers (`quant::bs`, `quant::mc`, `quant::pde`, `quant::american`, `quant::heston`, `quant::risk`).
- QMC components (`src/qmc/*`, `include/quant/qmc/*`) are used by Monte Carlo engines.

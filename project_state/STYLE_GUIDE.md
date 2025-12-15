# Style Guide

- **C++**
  - Use existing namespaces (`quant::bs`, `quant::mc`, `quant::pde`, `quant::american`, etc.). Prefer free functions + simple structs over heavy classes.
  - Naming: snake_case for functions/variables; PascalCase for enums; structs with public fields for parameter packs.
  - Keep headers lightweight; implementations live in `src/`; inline only small math helpers.
  - Error handling: validate inputs early (positive spot/strike, grid sizes ≥3, steps≥1); throw `std::invalid_argument` for misuse; clamp degenerate cases consistently (see BS, implied-vol, QE guards).
  - Determinism: prefer counter-based RNG (`quant::rng::Mode::Counter`) and streaming Welford accumulators; avoid storing full path arrays when not needed.
  - Grid-related code: reuse `grid_utils::build_space_grid` and `assemble_operator`; document stretching/BC choices briefly when adding new PDE variants.
  - Threading: guard OpenMP-specific code with `#ifdef QUANT_HAS_OPENMP`; keep RNG seeding deterministic per thread.
  - Comments: short, purpose-driven; avoid restating obvious assignments.

- **Python**
  - Follow existing module layout: top-level functions, dataclasses where helpful, minimal globals. Keep Pandas pipelines explicit.
  - Plotting: use `matplotlib.use("Agg")` for headless runs; write figures to provided paths; close figures to release memory.
  - Manifest logging: use `manifest_utils.update_run` for any script producing artifacts; include inputs/flags/seeds in payload.
  - Data handling: never write raw WRDS/IvyDB tables; only aggregated CSV/PNGs under `docs/artifacts/wrds/`. Respect schema in `scripts/data/schema.md`.
  - CLI scripts: prefer argparse with explicit defaults; provide `--fast` for quick smoke paths; keep outputs deterministic (fixed seeds) unless randomness is core to experiment.

- **Bindings / API**
  - Expose new C++ APIs through both CLI and pybind when broadly useful; mirror naming across C++/Python (e.g., McParams fields).
  - Keep Sobol dimension limits and barrier parity documented when surfacing new options.

- **Docs / Markdown**
  - Link to artifact CSV/PNG when quoting numbers; specify absolute dates (avoid “today”).
  - Keep roadmap/issues in sync with behavior changes; update `docs/artifacts/manifest.json` via scripts when regenerating figures.

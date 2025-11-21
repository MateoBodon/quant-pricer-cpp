# AGENTS.md

## Project overview

- `quant-pricer-cpp` is a modern C++20 option-pricing library:
  - Black–Scholes analytics, Monte Carlo (variance reduction, pathwise/LR Greeks, QMC), Crank–Nicolson PDE, barriers, American, exotics, Heston analytic + QE MC.
  - Python bindings (`pyquant_pricer`) and a CLI (`quant_cli`) wrap the C++ core.
  - Tests, Google Benchmark, coverage, and a deterministic artifact pipeline live under `docs/artifacts/`.

When in doubt: **extend existing patterns and scripts instead of inventing new ones.**

---

## Setup & build

From the repo root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Tests:

- Full suite (run before committing pricing changes): `ctest --test-dir build --output-on-failure`
- Fast loop while iterating: `ctest --test-dir build -L FAST --output-on-failure`

Optional local Python rebuild: `pip install -e .`

---

## WRDS data, comparison, and MARKET tests

Environment for live IvyDB pulls: set `WRDS_ENABLED=1`, `WRDS_USERNAME`, `WRDS_PASSWORD`. With no credentials the pipeline falls back to the bundled deterministic sample.

Primary pipeline commands (always prefer the existing scripts):

```bash
# Sample bundle (deterministic, no credentials)
python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample --fast

# Live IvyDB (opt-in, requires env)
WRDS_ENABLED=1 python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --fast
```

BS vs Heston comparison (reads existing artifacts only):

```bash
python -m wrds_pipeline.compare_bs_heston --wrds-root docs/artifacts/wrds
```

MARKET tests:

- Command: `ctest --test-dir build -L MARKET --output-on-failure`
- Behaviour: skips cleanly with exit code 77 unless `WRDS_ENABLED=1` with credentials. When enabled, runs a two-date `--fast` WRDS pipeline subset and asserts that headline metrics sit inside reasonable bands, then checks the comparison CSV/plots exist.
- The MARKET test writes to a temporary artifact root; it does not touch `docs/artifacts/wrds/`.

Rules for agents:

- ✅ Prefer real WRDS runs when `WRDS_ENABLED=1` is present.
- ✅ Only commit aggregated outputs under `docs/artifacts/wrds/` (pricing/oos/pnl CSVs, PNGs, comparison CSV/plots).
- ❌ Never commit raw IvyDB tables or credentials; never print secrets in logs.

---

## What to run before committing pricing/WRDS changes

- `cmake --build build -j`
- `ctest --test-dir build -L FAST --output-on-failure` (run full suite if pricing logic changed).
- WRDS sample refresh (or live if env set): `python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample --fast`
- BS vs Heston comparison regeneration: `python -m wrds_pipeline.compare_bs_heston --wrds-root docs/artifacts/wrds`
- For major releases: `WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

If you touch specific engines also run:

- Monte Carlo: `python scripts/mc_greeks_ci.py ...` and/or `python scripts/qmc_vs_prng_equal_time.py ...`
- PDE: `python scripts/pde_order_slope.py ...`
- Heston QE: `python scripts/heston_qe_vs_analytic.py ...`
- QuantLib parity: `python scripts/ql_parity.py ...`

---

## Code style & conventions

- C++20, clang-format and clang-tidy as configured in the repo.
- Prefer existing `quant::` namespaces (`quant::bs`, `quant::mc`, `quant::pde`, `quant::heston`, ...).
- Use `apply_patch` style edits; avoid wholesale rewrites.
- New modules go under `include/quant/` (headers) and `src/` (implementation); add tests under `tests/` and wire into CMake (and Python bindings when needed).

---

## Data & artifacts

- Only aggregated WRDS outputs belong in git: `docs/artifacts/wrds/wrds_agg_pricing*.csv`, `wrds_agg_oos*.csv`, `wrds_agg_pnl*.csv`, summary PNGs, and the BS-vs-Heston comparison CSV/plots.
- Do not commit temporary CSVs/PNGs elsewhere. Keep docs (Results/WRDS_Results/ROADMAP) and artifacts in sync when behaviour changes.

---

## Git etiquette

- Small, focused commits with messages like:
  - `fix heston qe bias for high vol-of-vol`
  - `add barrier mc edge-case tests`
  - `update wrds oos metrics and summary`
- Never force-push or reset history without explicit instruction.
- If unrelated changes exist locally, do not revert them—work around or ask.

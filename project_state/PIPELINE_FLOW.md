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

# Pipeline Flow

## Build & test flow
- Configure + build (Release):
  - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
  - `cmake --build build -j`
- Tests:
  - Fast loop: `ctest --test-dir build -L FAST --output-on-failure`
  - Full suite: `ctest --test-dir build --output-on-failure`
  - Market/WRDS: `ctest --test-dir build -L MARKET --output-on-failure` (skips unless `WRDS_ENABLED=1`).

## CLI flow
- Build `quant_cli` (`src/main.cpp`), then run:
  - `build/quant_cli bs ...`
  - `build/quant_cli mc ...`
  - `build/quant_cli pde ...`
  - `build/quant_cli american ...`
  - `build/quant_cli heston ...`

## Python bindings flow
- Build with scikit-build (`pyproject.toml`): `pip install -e .`
- Module name: `pyquant_pricer` (see `python/pybind_module.cpp`).

## Artifact reproduction flow
- All-in-one: `./scripts/reproduce_all.sh` (builds, runs FAST/SLOW tests, produces figures, updates manifest).
- Individual artifacts:
  - `python scripts/qmc_vs_prng_equal_time.py --output docs/artifacts/qmc_vs_prng_equal_time.png --csv docs/artifacts/qmc_vs_prng_equal_time.csv`
  - `python scripts/pde_order_slope.py --output docs/artifacts/pde_order_slope.png --csv docs/artifacts/pde_order_slope.csv`
  - `python scripts/tri_engine_agreement.py --quant-cli build/quant_cli --output docs/artifacts/tri_engine_agreement.png --csv docs/artifacts/tri_engine_agreement.csv`
  - `python scripts/heston_qe_vs_analytic.py --quant-cli build/quant_cli --output docs/artifacts/heston_qe_vs_analytic.png --csv docs/artifacts/heston_qe_vs_analytic.csv`
  - `python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json`

## WRDS pipeline flow
- Single-date or panel runs: `python -m wrds_pipeline.pipeline [--symbol SPX] [--trade-date YYYY-MM-DD] [--use-sample] [--fast]`.
- Multi-date panel uses `wrds_pipeline_dates_panel.yaml` (invoked automatically in `scripts/reproduce_all.sh`).
- BS vs Heston comparison: `python -m wrds_pipeline.compare_bs_heston --wrds-root docs/artifacts/wrds`.

## Packaging/release flow
- Validation pack: `python scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip`.
- Makefile targets: `make bench` (see `project_state/_generated/make_targets.txt`).

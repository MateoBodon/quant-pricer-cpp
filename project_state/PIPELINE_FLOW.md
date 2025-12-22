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

# Pipeline Flow

## Build & test flow
- Configure + build (Release):
  - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
  - `cmake --build build -j`
- Tests:
  - Fast loop: `ctest --test-dir build -L FAST --output-on-failure`
  - Full suite: `ctest --test-dir build --output-on-failure`
  - Market/WRDS: `ctest --test-dir build -L MARKET --output-on-failure` (skips without WRDS env).

## CLI flow
- Build `quant_cli` (`src/main.cpp`), then run:
  - `build/quant_cli bs ...`
  - `build/quant_cli mc ...`
  - `build/quant_cli pde ...`
  - `build/quant_cli american ...`
  - `build/quant_cli heston ...`
  - `build/quant_cli risk ...`

## Python bindings flow
- Build with scikit-build (`pyproject.toml`): `pip install -e .`
- Module name: `pyquant_pricer` (see `python/pybind_module.cpp`).

## Artifact reproduction flow
- All-in-one: `./scripts/reproduce_all.sh` (builds, runs FAST tests, produces figures, updates manifest).
- Individual artifacts (examples):
  - `python scripts/qmc_vs_prng_equal_time.py --output docs/artifacts/qmc_vs_prng_equal_time.png --csv docs/artifacts/qmc_vs_prng_equal_time.csv`
  - `python scripts/pde_order_slope.py --output docs/artifacts/pde_order_slope.png --csv docs/artifacts/pde_order_slope.csv`
  - `python scripts/tri_engine_agreement.py --quant-cli build/quant_cli --output docs/artifacts/tri_engine_agreement.png --csv docs/artifacts/tri_engine_agreement.csv`
  - `python scripts/heston_qe_vs_analytic.py --quant-cli build/quant_cli --output docs/artifacts/heston_qe_vs_analytic.png --csv docs/artifacts/heston_qe_vs_analytic.csv`
  - `python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json`

## Data-policy guard flow
- Guard script: `python3 scripts/check_data_policy.py` (scans tracked CSVs under `artifacts/`, `docs/artifacts/`, `data/`, `wrds_pipeline/sample_data/`).
- FAST test: `ctest --test-dir build -L FAST --output-on-failure` includes `test_data_policy_fast`.

## WRDS pipeline flow
- Single-date or panel runs: `python -m wrds_pipeline.pipeline [--symbol SPX] [--trade-date YYYY-MM-DD] [--use-sample] [--fast]`.
- Multi-date panel uses `wrds_pipeline_dates_panel.yaml` (invoked automatically in `scripts/reproduce_all.sh`).
- BS vs Heston comparison: `python -m wrds_pipeline.compare_bs_heston --wrds-root docs/artifacts/wrds`.
- Local cache builder: `python scripts/build_wrds_cache.py --symbol SPX --start-date YYYY-MM-DD --end-date YYYY-MM-DD`.

## Packaging / bundle flow
- Validation pack: `python scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip`.
- GPT bundle: `python scripts/gpt_bundle.py --ticket <ticket-XX> --run-name <RUN_NAME> [--timestamp ...]`.
- Makefile targets: `make bench`, `make gpt-bundle` (see `project_state/_generated/make_targets.txt`).

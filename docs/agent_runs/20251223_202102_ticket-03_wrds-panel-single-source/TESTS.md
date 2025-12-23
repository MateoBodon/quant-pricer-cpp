# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` (pass)
- `cmake --build build -j` (pass)
- `ctest --test-dir build -L FAST --output-on-failure` (pass; 1 skipped: `RngDeterminism.CounterRngThreadInvariant` due to OpenMP not enabled)
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` (pass; single-date sample run)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (pass; rerun after an accidental interrupted invocation to restore artifacts)

Key output snippets:
- `[wrds_pipeline] dateset=/Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp/wrds_pipeline_dates_panel.yaml panel_id=wrds_panel_calm_stress_v1 entries=5`
- `docs/artifacts/manifest.json` includes `runs.wrds_dateset[].panel_id=wrds_panel_calm_stress_v1` and `dateset_inputs` with the config hash.

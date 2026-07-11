# Commands

Working directory: repository root.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 tests/test_wrds_local_metrics_one_command_fast.py
PYTHONDONTWRITEBYTECODE=1 WRDS_USE_SAMPLE=1 .venv/bin/python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml --use-sample
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 tests/test_metrics_snapshot_fast.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 scripts/check_data_policy.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 tests/test_docs_sanity_fast.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 tests/test_wrds_realdata_export_fast.py
cmake --build build -j 4
PATH="$PWD/.venv/bin:$PATH" ctest --test-dir build -L FAST --output-on-failure
```

Exact corrected local-vault replay from stable implementation commit
`2ccbf54305a40925e5ed9c8003e3ae803000b41d`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
PATH="$PWD/.venv/bin:$PATH" \
WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds \
QUANT_MACHINE_LABEL=portfolio-admin-local \
MPLCONFIGDIR=/tmp/quant-pricer-mpl \
./scripts/reproduce_wrds_local_metrics.sh \
  --dateset wrds_pipeline_dates_panel.yaml \
  --run-id wrds_local_20260711T160500Z_claim_integrity_v3
```

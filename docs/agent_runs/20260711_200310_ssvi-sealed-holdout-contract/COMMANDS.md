# Commands

Working directory:
`/Volumes/Storage/Projects/quant-pricer-cpp/repo`

```bash
shasum -a 256 \
  wrds_pipeline_dates_panel_resume_v2.yaml \
  wrds_pipeline_dates_ssvi_holdout_v1.yaml \
  configs/ssvi_temporal_holdout_v1.json

.venv/bin/python -m py_compile \
  scripts/ssvi_holdout_preflight.py \
  scripts/ssvi_sealed_holdout.py \
  tests/test_ssvi_holdout_contract_fast.py

.venv/bin/python tests/test_ssvi_holdout_contract_fast.py
.venv/bin/python scripts/ssvi_holdout_preflight.py --check-contract-only

WRDS_LOCAL_ROOT="${trusted_vault_root}" \
  .venv/bin/python scripts/ssvi_holdout_preflight.py \
  --output artifacts/_local/wrds_local/ssvi_holdout_preflight_v1.json
```

The metadata preflight reads compressed bytes only to calculate SHA-256 and
checks acquisition-manifest status, size, and row-count metadata. The sealed
outcome runner is deliberately not invoked in this run.

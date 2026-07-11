# Commands

Working directory:
`/Volumes/Storage/Projects/quant-pricer-cpp/repo`

```bash
.venv/bin/python -m py_compile \
  scripts/ssvi_development_benchmark.py \
  scripts/ssvi_five_date_panel.py \
  tests/test_ssvi_surface_fast.py

.venv/bin/python tests/test_ssvi_surface_fast.py

.venv/bin/python scripts/ssvi_five_date_panel.py \
  --run-root artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3 \
  --output artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3/ssvi_five_date_panel.json

.venv/bin/python scripts/check_data_policy.py
.venv/bin/python tests/test_docs_sanity_fast.py

project-os-v3 verify \
  --project-id quant-pricer-cpp \
  --goal goal_761f3b87e713 \
  --profile strict \
  --summary
```

The panel command hard-codes all five predeclared pairs and requires exactly
1,239 calibration rows. Its aggregate-only JSON receipt stays under the ignored
local artifact root.

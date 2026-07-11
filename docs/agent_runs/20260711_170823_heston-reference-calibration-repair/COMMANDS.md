# Commands

Working directory:
`/Volumes/Storage/Projects/quant-pricer-cpp/repo`

```bash
.venv/bin/python tests/test_wrds_local_metrics_one_command_fast.py

.venv/bin/python scripts/heston_reference_audit.py \
  --run-root artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3 \
  --output artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3/heston_reference_audit.json

.venv/bin/python scripts/heston_calibration_repair_audit.py \
  --run-root artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3 \
  --dates 2020-03-16 2024-06-14 \
  --max-evals 160 \
  --output artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3/heston_calibration_repair_audit.json
```

The two audit receipts are aggregate-only and remain under the ignored local
artifact root. Raw and row-level OptionMetrics data are not copied into Git.

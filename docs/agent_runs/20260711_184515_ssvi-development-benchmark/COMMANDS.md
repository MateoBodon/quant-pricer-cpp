# Commands

Working directory:
`/Volumes/Storage/Projects/quant-pricer-cpp/repo`

```bash
.venv/bin/python tests/test_ssvi_surface_fast.py

.venv/bin/python scripts/ssvi_development_benchmark.py \
  --run-root artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3 \
  --output artifacts/_local/wrds_local/wrds_local_20260711T160500Z_claim_integrity_v3/ssvi_development_benchmark.json

project-os-v3 verify \
  --project-id quant-pricer-cpp \
  --goal goal_41cd2848fa46 \
  --profile strict \
  --summary
```

The benchmark command enforces the predeclared date pairs in code. Its JSON
receipt is aggregate-only and remains under the ignored local artifact root.

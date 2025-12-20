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

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-18T18:55:29Z**).

Status summary (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: missing
- benchmarks: missing
- wrds: missing

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- The metrics snapshot reports missing artifacts for QL parity, benchmarks, and WRDS at generation time; see `project_state/KNOWN_ISSUES.md`.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

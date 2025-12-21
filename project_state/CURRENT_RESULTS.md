---
generated_at: 2025-12-21T20:30:38Z
git_sha: 30002fe1a2fd69644b54a36237b8d820da8743f0
branch: feature/ticket-06-wrds-local-guardrails
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
  - python3 scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
  - rg -n "ql parity|benchmarks|wrds" docs/artifacts/metrics_summary.md
---

# Current Results

## Metrics snapshot (latest committed)
Source: `docs/artifacts/metrics_summary.md` (generated at **2025-12-21T20:29:56.983890+00:00**).

Status summary (from `docs/artifacts/metrics_summary.md`):
- tri engine agreement: ok
- qmc vs prng equal time: ok
- pde order: ok
- ql parity: ok
- benchmarks: ok
- wrds: ok

## Key artifact locations
- Validation figures + CSVs: `docs/artifacts/` (tri-engine, QMC vs PRNG, PDE order, MC Greeks, Heston QE, etc.).
- Manifest metadata: `docs/artifacts/manifest.json`.
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`.
- WRDS aggregated outputs (if present): `docs/artifacts/wrds/`.
- Validation bundle: `docs/validation_pack.zip`.

## Notes
- The metrics snapshot reports no missing artifacts for QL parity, benchmarks, or WRDS sample outputs.
- Narrative results live in `docs/Results.md`, `docs/Validation*.md`, and `docs/WRDS_Results.md` (sample bundle).

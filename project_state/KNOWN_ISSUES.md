---
generated_at: 2025-12-21T20:30:38Z
git_sha: 30002fe1a2fd69644b54a36237b8d820da8743f0
branch: feature/ticket-06-wrds-local-guardrails
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - rg -n "ql parity|benchmarks|wrds" docs/artifacts/metrics_summary.md
---

# Known Issues

- `ROADMAP (1).md` notes Heston QE bias remains under investigation; QE is still described as experimental in roadmap notes.
- WRDS live runs are gated by environment variables (`WRDS_ENABLED=1` + credentials); MARKET tests skip without them (`wrds_pipeline/tests/test_wrds_pipeline.py`).
- Prior local-run WRDS artifacts under `docs/artifacts/wrds/per_date/` contained strike/IV surfaces derived from real data, which risks redistribution; keep committed WRDS artifacts sample-only and isolate any local/live outputs under `docs/artifacts/wrds_local/` or external paths.

---
generated_at: 2025-12-20T22:52:41Z
git_sha: cf1d770d18d26b8db15c0638c692ac50f5f2747e
branch: feature/ticket-01-artifact-completeness
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - rg -n "ql parity|benchmarks|wrds" docs/artifacts/metrics_summary.md
---

# Known Issues

- `ROADMAP (1).md` notes Heston QE bias remains under investigation; QE is still described as experimental in roadmap notes.
- WRDS live runs are gated by environment variables (`WRDS_ENABLED=1` + credentials); MARKET tests skip without them (`wrds_pipeline/tests/test_wrds_pipeline.py`).

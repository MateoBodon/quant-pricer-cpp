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

# Known Issues

- `docs/artifacts/metrics_summary.md` flags missing artifacts for QL parity, benchmarks, and WRDS at the last snapshot (generated 2025-12-18).
- `ROADMAP (1).md` notes Heston QE bias remains under investigation; QE is still described as experimental in roadmap notes.
- WRDS live runs are gated by environment variables (`WRDS_ENABLED=1` + credentials); MARKET tests skip without them (`wrds_pipeline/tests/test_wrds_pipeline.py`).

---
generated_at: 2025-12-22T00:21:44Z
git_sha: ae2691df74d6b813e23a231ee5308a6573456f45
branch: main
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - rg -n "strike,.*market_iv" -S .
  - rg -n "\\bsecid\\b|best_bid|best_ask|best_offer" -S .
---

# Known Issues

- `ROADMAP (1).md` notes Heston QE bias remains under investigation; QE is still described as experimental in roadmap notes.
- WRDS live runs are gated by environment variables (`WRDS_ENABLED=1` + credentials); MARKET tests skip without them (`wrds_pipeline/tests/test_wrds_pipeline.py`).
- Prior local-run WRDS artifacts under `docs/artifacts/wrds/per_date/` contained strike/IV surfaces derived from real data, which risks redistribution; keep committed WRDS artifacts sample-only and isolate any local/live outputs under `docs/artifacts/wrds_local/` or external paths.
- (Resolved 2025-12-22) Removed tracked Heston fit tables with `strike`/`market_iv` columns and added a data-policy guard to block reintroducing restricted columns in tracked artifacts.

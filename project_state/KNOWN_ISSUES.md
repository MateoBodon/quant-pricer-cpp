---
generated_at: 2025-12-22T19:13:19Z
git_sha: 5265c6de1a7e13f4bfc8708f188986cee30b18ed
branch: feature/ticket-00_project_state_refresh
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - c++ --version
  - cmake --version
  - uname -a
  - rg --files
  - rg --files -g '*.py'
  - rg --files tests
  - rg -n "argparse|click|typer" scripts wrds_pipeline python tests tools
  - python3 tools/project_state_generate.py
---

# Known Issues

- Heston QE bias remains under investigation (see `ROADMAP (1).md` and `docs/Results.md` notes).
- WRDS live runs are gated by environment variables (`WRDS_ENABLED=1` + credentials); MARKET tests skip without them (`wrds_pipeline/tests/test_wrds_pipeline.py`).
- RESOLVED (2025-12-23): WRDS pipeline previously lacked explicit as-of guards for `quote_date` mismatches in calibration/OOS; hard checks and poison FAST tests added. Run log: `docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/`.
- Live/local WRDS outputs must not be committed; keep them outside the repo or under gitignored paths such as `docs/artifacts/wrds_local/` (data-policy guard enforces restricted-column rules).
- Local WRDS runs update `docs/artifacts/manifest.json` by default; keep the canonical manifest sample-only and store local provenance in `docs/artifacts/wrds_local/manifest_local.json` (untracked).
- Script defaults are split between `docs/artifacts/` and `artifacts/`, which can lead to confusion if the wrong artifact root is used in summaries.

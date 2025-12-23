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

# Open Questions

- `ROADMAP (1).md` is the active roadmap source; should it be renamed/moved to `docs/ROADMAP.md` to match references in the roadmap text?
- Artifact outputs are split between `docs/artifacts/` (repro pipeline) and `artifacts/` (several scripts default here). Should defaults be unified to avoid confusion?
- Both `docs/artifacts/manifest.json` and `artifacts/manifest.json` exist. Which one is canonical for downstream consumers?

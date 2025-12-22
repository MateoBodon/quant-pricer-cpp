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

# Server Environment

## Runtime snapshot
- OS: Darwin Mateos-MacBook-Pro-7.local 25.0.0 (arm64) (`uname -a`).
- Python: 3.12.2 (`python3 -V`).
- CMake: 4.1.2 (`cmake --version`).
- C++ compiler: Apple clang 17.0.0 (`c++ --version`).

## Notes
- Package lists were not captured to avoid heavy environment scanning.
- WRDS credentials are not present in repo; live runs require env vars (`WRDS_ENABLED`, `WRDS_USERNAME`, `WRDS_PASSWORD`).

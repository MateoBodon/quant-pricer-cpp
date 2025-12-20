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

# Server Environment

## Runtime snapshot
- OS: Darwin Mateos-MacBook-Pro-7.local 25.0.0 (arm64) (`uname -a`).
- Python: 3.12.2 (`python3 -V`).
- CMake: 4.1.2 (`cmake --version`).

## Notes
- Package lists were not captured to avoid heavy environment scanning.
- WRDS credentials are not present in repo; live runs require env vars (`WRDS_ENABLED`, `WRDS_USERNAME`, `WRDS_PASSWORD`).

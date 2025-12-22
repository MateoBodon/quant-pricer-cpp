# Tests

- `python3 -m compileall scripts/gpt_bundle.py` — **PASSED**.
- `make gpt-bundle TICKET=ticket-06b RUN_NAME=20251222_014941_ticket-06b_bundle-integrity TIMESTAMP=20251222T015729Z` — **PASSED**.
- `python3 scripts/gpt_bundle.py --ticket ticket-06b --run-name 20251222_014941_ticket-06b_bundle-integrity --timestamp 20251222T015729Z` (with `PROGRESS.md` temporarily moved) — **EXPECTED FAIL** (exit=1, missing PROGRESS.md).
- `ctest --test-dir build -L FAST --output-on-failure` — **SKIPPED** (bundler-only change; build dir not validated in this run).

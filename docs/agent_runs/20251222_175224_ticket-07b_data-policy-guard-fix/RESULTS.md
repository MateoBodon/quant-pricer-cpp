# Results

## Step 1 — Ticket-07 inspection
- Read `docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/{RESULTS.md,TESTS.md,COMMANDS.md,META.json}`.
- `git status --porcelain`:
  ```
  ?? docs/agent_runs/20251222_175224_ticket-07b_data-policy-guard-fix/
  ```
- `git ls-files scripts/check_data_policy.py tests/test_data_policy_fast.py`:
  ```
  scripts/check_data_policy.py
  tests/test_data_policy_fast.py
  ```
- `artifacts/heston/README.md` is present and tracked.

## Changes
- Enforced `# SYNTHETIC_DATA` markers for tracked CSVs under `wrds_pipeline/sample_data/` in `scripts/check_data_policy.py` (prevents rename-only bypasses).
- Replaced `wrds_pipeline/sample_data/spx_options_sample.csv` with a small, explicitly synthetic Black–Scholes-derived sample (80 rows) and added the marker line.
- Updated the sample loader to skip comment lines (`comment="#"`).
- Added `requirements-dev.txt` and documented `pip install -r requirements-dev.txt` in `CONTRIBUTING.md` to cover matplotlib for FAST tests.
- Updated `AGENTS.md`, `docs/CODEX_SPRINT_TICKETS.md` (Ticket-07b), `project_state/KNOWN_ISSUES.md`, `PROGRESS.md`, and `CHANGELOG.md`.

## Tests
- FAST initially failed due to `matplotlib` missing in the Python3.13 interpreter; reconfigured CMake to use Python 3.12 and FAST passed (see `TESTS.md`).
- Sample-mode WRDS pipeline smoke run succeeded with `source_today=sample` and `source_next=sample`.

## Bundle
- `docs/gpt_bundles/20251222T181613Z_ticket-07b_20251222_175224_ticket-07b_data-policy-guard-fix.zip`

## Human merge checklist
- [x] New guard + test files are tracked and appear in git diff
- [x] No WRDS/raw market data committed
- [x] FAST is green
- [x] Sample-mode pipeline smoke succeeded
- [x] Run log folder complete
- [x] Bundle contains required items and correct SHAs

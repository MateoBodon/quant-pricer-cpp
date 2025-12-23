You are a coding agent operating in the `quant-pricer-cpp` repository.

BEGIN by reading these files (in order):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-02 — WRDS as-of correctness hard checks + poison-pill tests (sample mode)

Non-negotiable (stop-the-line):
- Do NOT fabricate results or claim commands ran if they did not (log everything).
- Do NOT commit raw WRDS/OptionMetrics data or leak credentials into logs.
- Do NOT “fix” validity by weakening evaluation (no silent filtering unless explicitly specified and logged).
- Follow DOCS_AND_LOGGING_SYSTEM.md: create run log folder + required files.

Goal (1 sentence):
Add automated checks that catch quote_date/trade_date mismatches and prevent lookahead in WRDS calibration and OOS evaluation (sample mode).

Acceptance criteria (must satisfy all):
1) Calibration step hard-fails (preferred) OR filters-to-zero (only if explicitly configured/logged) if any row has `quote_date != trade_date`.
2) OOS evaluation hard-fails if any row has `quote_date != next_trade_date`.
3) A FAST test injects a “poison” sample file and verifies the pipeline rejects it (non-zero exit / raised exception + clear message).
4) Outputs include provenance fields for `trade_date` and `next_trade_date` (written into whatever provenance JSON/manifest the WRDS pipeline emits).

Required workflow (do NOT write a long upfront plan):
1) Create a new run log folder:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-02_wrds-asof-checks"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json (and SOURCES.md only if web research used).
   - Put this entire prompt text into PROMPT.md.
   - Start COMMANDS.md immediately and append every command you run.

2) Inspect the WRDS pipeline code + sample data schema:
   - Locate entrypoints:
     - `wrds_pipeline/pipeline.py`
     - calibration module(s): `wrds_pipeline/calibrate_*.py`
     - OOS module(s): `wrds_pipeline/oos_pricing.py` (or equivalent)
     - ingest module(s): `wrds_pipeline/ingest_*.py`
     - existing tests: `wrds_pipeline/tests/*` and/or CTest FAST python tests
   - Identify where `quote_date`, `trade_date`, and `next_trade_date` are:
     - parsed
     - compared
     - used to select calibration/OOS rows

3) Implement hard checks (fail-closed, with clear error messages):
   - Calibration:
     - Before fitting, assert ALL rows used satisfy `quote_date == trade_date`.
     - If violated: raise a clear exception (include a small sample of offending rows/ids, but no secrets).
   - OOS evaluation:
     - Before computing OOS errors, assert ALL rows used satisfy `quote_date == next_trade_date`.
     - If violated: raise a clear exception.

4) Add poison-pill test in sample mode:
   - Add a small synthetic sample fixture (license-safe) with `# SYNTHETIC_DATA` marker if it is a CSV under `wrds_pipeline/sample_data/`.
   - The poison should include at least one row where:
     - calibration poison: `quote_date != trade_date`, OR
     - oos poison: `quote_date != next_trade_date`
   - Add a FAST test that runs the sample pipeline against the poison input and asserts it FAILS.
   - IMPORTANT: do not rely on global mutable state; make the test deterministic.
   - If the pipeline currently cannot be pointed at an alternate sample root/file, add a minimal config/env override to do so (document it).

5) Provenance outputs:
   - Ensure the WRDS pipeline writes `trade_date` and `next_trade_date` into its provenance output(s):
     - e.g., a per-run JSON, a manifest entry, or a dedicated provenance file under `docs/artifacts/wrds/` in sample mode.
   - If there is already a provenance schema, extend it minimally and update any readers accordingly.

6) Run minimal sufficient tests (log in TESTS.md with outputs):
   - Build + FAST tests (per AGENTS.md):
     - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
     - `cmake --build build -j`
     - `ctest --test-dir build -L FAST --output-on-failure`
   - Sample-mode real-data smoke (must run, not just unit tests):
     - Prefer: `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
     - If `python` is on PATH instead, `python -m wrds_pipeline.pipeline --fast` is fine — record what you used.
   - Confirm the poison-pill test fails before fix (if you can demonstrate) and passes after fix by asserting the pipeline now rejects poison input.

7) Update docs:
   - PROGRESS.md: add a dated entry with:
     - what changed
     - exact tests run
     - sample pipeline command used
   - If you discover an existing as-of leakage behavior: update `project_state/KNOWN_ISSUES.md` with:
     - the issue
     - the fix
     - link to this run log folder
   - If you add/rename env vars or config knobs: update `project_state/CONFIG_REFERENCE.md` (or the appropriate source doc).

8) Commit on a feature branch:
   - `git switch -c codex/ticket-02-wrds-asof-checks`
   - Commit message: `ticket-02: WRDS as-of correctness gates + poison tests`
   - Commit body must include:
     - `Tests: <exact commands>`
     - `Artifacts: <paths updated or 'none'>`
     - `Run log: docs/agent_runs/${RUN_NAME}/`

9) Generate the next review bundle at the end (and record the bundle path in RESULTS.md):
   - `make gpt-bundle TICKET=ticket-02 RUN_NAME=${RUN_NAME}`

Suggested Codex invocation (safe mode; approvals on):
- `codex --profile safe`

Human merge checklist (append to RESULTS.md):
- Poison-pill test fails without the fix and fails-closed in production paths
- Sample pipeline smoke ran successfully in WRDS_USE_SAMPLE=1 mode
- No raw WRDS extracts or credentials committed or printed
- PROGRESS.md updated; KNOWN_ISSUES/CONFIG_REFERENCE updated if impacted
- Bundle generated via make gpt-bundle and contains complete non-empty run logs

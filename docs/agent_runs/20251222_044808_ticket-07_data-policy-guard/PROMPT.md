You are Codex working on quant-pricer-cpp.

FIRST read these files (in this order) and treat them as binding:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-07 — Data policy cleanup + automated “no quote surfaces” guard

Do NOT write a long upfront plan. Do the work.

## Goal
Eliminate license/compliance landmines by removing or replacing quote-surface shaped artifacts (e.g., per-strike “market_iv” grids) and adding an automated guard that prevents committing anything that looks like raw/redistributable WRDS/OptionMetrics outputs.

## Stop-the-line reminders
- Do NOT commit raw WRDS/OptionMetrics tables, parquet exports, quote-level surfaces, or credentials.
- If you find tracked files that look like redistributed market data, STOP, document, and remove/quarantine them safely.

## Acceptance criteria (objective)
1) Implement `scripts/check_data_policy.py` that:
   - scans *git-tracked* files (use `git ls-files`) for prohibited patterns:
     - `strike,.*market_iv`
     - `\bsecid\b`
     - `best_bid|best_ask|best_offer`
   - allows matches in code/docs (e.g., `.py`, `.hpp`, `.md`) but FAILS if matches appear in tracked data/artifact files (`.csv`, `.parquet`, `.json` under artifacts-like directories).
   - exits non-zero and prints offending file paths + matching lines.
2) Resolve existing violations:
   - Remove/quarantine any tracked quote-surface shaped artifact files (e.g., `artifacts/heston/fit_*.csv` / `artifacts/heston/series_runs/fit_*.csv` if present).
   - If the project truly needs an example of that schema, replace with clearly synthetic/public-source sample and document provenance in a short README in that directory.
3) Add enforcement:
   - Run `python3 scripts/check_data_policy.py` in FAST (either as a Python test or as part of `./scripts/reproduce_all.sh` in FAST mode).
4) Update docs:
   - Update `project_state/KNOWN_ISSUES.md` (mark the issue resolved or precisely scoped).
   - Update `PROGRESS.md`.
   - If you add any new policy rule, reflect it in `AGENTS.md`.

## Implementation steps
1) Inspect repository for violations using ripgrep and git-tracked list:
   - `git ls-files | wc -l`
   - `git ls-files | rg -n "\.(csv|parquet|json)$" -S`
   - `git ls-files | xargs rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S`
2) Implement `scripts/check_data_policy.py` with clear allow/deny logic.
3) Remove or replace offending tracked artifacts (do not rewrite history; just fix HEAD).
4) Add a minimal FAST guard (choose one):
   - Python test: `tests/test_data_policy_fast.py` that runs the script and asserts exit 0, OR
   - Add it to `ctest -L FAST` suite if there is an existing Python FAST runner, OR
   - Add to `./scripts/reproduce_all.sh` with `REPRO_FAST=1` (less ideal than tests, but acceptable).

## Required run log folder (mandatory)
RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-07_data-policy-guard"

Create `docs/agent_runs/$RUN_NAME/` containing:
- PROMPT.md (paste this prompt verbatim)
- COMMANDS.md (every command executed, in order; no ellipsizing)
- RESULTS.md (what changed + before/after scan outputs + paths removed/replaced)
- TESTS.md (tests run + outputs)
- META.json (git_sha_before/after, branch, env notes)

## Minimal tests/commands to run (must log them)
- `python3 -m compileall scripts/check_data_policy.py`
- `python3 scripts/check_data_policy.py`
- If a build exists, also run FAST:
  - `ctest --test-dir build -L FAST --output-on-failure`
- Small “real-data smoke” (sample mode, credential-free) if WRDS pipeline is touched by removals:
  - `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
  (If not touched, you may skip, but say so explicitly in TESTS.md.)

## Commit policy (mandatory)
- Branch: `feature/ticket-07_data-policy-guard`
- Commit message: `ticket-07: data policy guard + remove quote-surface artifacts`
- Commit body MUST include:
  - `Tests: <exact commands>`
  - `Run log: docs/agent_runs/$RUN_NAME/`
  - `Removed/Changed: <key paths>`

## Generate the next review bundle (mandatory)
At the end:
- `make gpt-bundle TICKET=ticket-07 RUN_NAME=$RUN_NAME`
Record the resulting bundle path in `docs/agent_runs/$RUN_NAME/RESULTS.md`.

## Suggested Codex invocation (safe)
Use sandbox + approvals:
- `codex --sandbox workspace-write --ask-for-approval on-request`

Full-autonomy mode is NOT requested.

## Human merge checklist (include at end of RESULTS.md)
- [ ] No tracked quote-surface artifacts remain (scan is clean)
- [ ] data policy guard script exists and passes
- [ ] FAST tests pass (if run)
- [ ] PROGRESS + project_state docs updated
- [ ] Bundle generated and contains required run logs + DIFF.patch + LAST_COMMIT.txt

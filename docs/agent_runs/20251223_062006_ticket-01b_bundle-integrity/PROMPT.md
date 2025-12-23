You are a coding agent operating in the `quant-pricer-cpp` repository.

BEGIN by reading these files (in order):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-01b — Bundle integrity + evidence repair (ticket-01)

Non-negotiable rules (stop-the-line):
- Do not fabricate results or claim commands ran if they did not.
- Do not commit raw WRDS/OptionMetrics data or leak credentials into logs.
- Do not “fix” by disabling functionality or weakening evaluation; if you discover validity risk, document + fix properly.
- Follow AGENTS.md and DOCS_AND_LOGGING_SYSTEM.md run logging requirements.

Goal (1 sentence):
Make `make gpt-bundle` reject empty run logs / incomplete evidence, produce a reviewable DIFF.patch for the ticket, and regenerate a correct ticket-01 bundle that includes the real implementation run evidence.

Acceptance criteria (must be satisfied):
1) Bundling hard-gates:
   - `make gpt-bundle ...` FAILS if any required run log file exists but is empty:
     - PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json
2) DIFF coverage:
   - The generated `DIFF.patch` spans the ticket’s substantive changes (scripts/tests), not only doc-only last-commit diffs.
3) Evidence repair:
   - You can generate a new ticket-01 bundle using the *actual* implementation run log folder (see PROGRESS.md for the correct run name, likely `20251222_204744_ticket-01_unify-artifacts`) and it includes:
     - non-empty run log files
     - a DIFF.patch that includes the artifact-root/manifest/test changes
4) Documentation:
   - Update PROGRESS.md with what you did and what commands you ran.
   - Update docs/CODEX_SPRINT_TICKETS.md:
     - mark ticket-01 as FAIL (evidence missing)
     - add ticket-01b with these acceptance criteria

Required workflow (do NOT write a long plan first):
1) Create a new run log folder:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-01b_bundle-integrity"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json
   - Put this entire prompt text into PROMPT.md.

2) Inspect current bundling implementation:
   - Locate `make gpt-bundle` (Makefile target) and the script it calls (likely `scripts/gpt_bundle.py`).
   - Identify:
     - how it selects the run log folder
     - how it builds DIFF.patch (what git range)
     - what validations exist (and why empty files didn’t fail)

3) Implement the hard gates:
   - Add checks that each required run-log file:
     - exists
     - size > 0 bytes (and ideally > a minimal threshold, e.g. > 20 chars)
   - If any required file fails, exit non-zero with a clear error that names the missing/empty file.

4) Fix DIFF.patch coverage:
   - Ensure DIFF.patch captures the ticket’s code changes. Implement one of:
     - Option A (preferred): accept an explicit BASE_SHA (env or flag) and diff BASE_SHA..HEAD
     - Option B: compute base as merge-base with main OR first commit matching the ticket prefix in commit messages (e.g., grep `ticket-01:`) and diff from that base..HEAD
   - Also include a short `git log --oneline <base>..HEAD` in the bundle (or in the run log RESULTS.md) so reviewers know what commits are covered.

5) Regenerate ticket-01 bundle using the correct run folder:
   - From PROGRESS.md, find the run log folder that actually ran tests + repro for ticket-01 (likely `docs/agent_runs/20251222_204744_ticket-01_unify-artifacts/`).
   - Verify that folder contains non-empty PROMPT/COMMANDS/RESULTS/TESTS/META.
   - Run:
     - `make gpt-bundle TICKET=ticket-01 RUN_NAME=20251222_204744_ticket-01_unify-artifacts`
   - Record the produced bundle path in your RESULTS.md.

6) Generate the ticket-01b bundle for this run:
   - Run:
     - `make gpt-bundle TICKET=ticket-01b RUN_NAME=${RUN_NAME}`
   - Record the produced bundle path in RESULTS.md.

7) Minimal tests to run (log them in TESTS.md):
   - For bundling script changes:
     - `python3 -m compileall scripts/gpt_bundle.py` (or the actual bundler script path)
   - Run a bundler self-check:
     - create a temporary run folder with empty required files and show `make gpt-bundle` fails as expected (document the command + error message snippet).
   - No WRDS or pricing engine runs required for this ticket unless you touch evaluation code.

8) Update docs:
   - Append a PROGRESS.md entry (date, summary, commands run, bundle paths).
   - Update docs/CODEX_SPRINT_TICKETS.md (ticket-01 status + add ticket-01b).

9) Commit on a feature branch:
   - `git switch -c codex/ticket-01b-bundle-integrity`
   - Commit message: `ticket-01b: harden gpt-bundle evidence gates`
   - Commit body must include:
     - `Tests: <exact commands>`
     - `Artifacts: <bundle paths or 'none'>`
     - `Run log: docs/agent_runs/${RUN_NAME}/`

Suggested Codex invocation (safe mode; approvals on):
- `codex --profile safe`

Human merge checklist (include at end of RESULTS.md):
- Bundle fails on empty run logs
- New ticket-01 bundle includes the implementation run log + a DIFF.patch with scripts/tests changes
- No secrets or raw WRDS data were committed
- PROGRESS + sprint tickets updated

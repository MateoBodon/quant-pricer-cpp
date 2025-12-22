You are Codex working on quant-pricer-cpp.

FIRST read these files (in this order) and treat them as binding:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-06b — Bundle + run-log completeness hard gate

Do NOT write a long upfront plan. Do the work.

## Goal
Fix the review loop: `make gpt-bundle` must produce an auditable bundle that always contains the required run log files, and it must fail fast if anything required is missing.

## Acceptance criteria (objective)
1) `make gpt-bundle TICKET=ticket-06b RUN_NAME=<RUN_NAME>` produces a zip that contains:
   - AGENTS.md
   - docs/PLAN_OF_RECORD.md
   - docs/DOCS_AND_LOGGING_SYSTEM.md
   - docs/CODEX_SPRINT_TICKETS.md
   - PROGRESS.md
   - project_state/CURRENT_RESULTS.md
   - project_state/KNOWN_ISSUES.md
   - project_state/CONFIG_REFERENCE.md
   - DIFF.patch
   - LAST_COMMIT.txt
   - docs/agent_runs/<RUN_NAME>/{PROMPT.md,COMMANDS.md,RESULTS.md,TESTS.md,META.json}
2) Bundling FAILS (exit code != 0) with a clear message listing missing files if any of the above are absent.
3) Bundling FAILS (exit code != 0) if `docs/CODEX_SPRINT_TICKETS.md` does not contain an entry for the ticket id (string match on "Ticket-06b" or "ticket-06b").
4) `PROGRESS.md` and `docs/CODEX_SPRINT_TICKETS.md` are updated for this ticket, and the run is logged under `docs/agent_runs/<RUN_NAME>/`.

## Implementation steps
1) Inspect the existing bundler:
   - scripts/gpt_bundle.py
   - Makefile (gpt-bundle target)
2) Modify scripts/gpt_bundle.py so it:
   - builds the required file list (above),
   - validates existence before zipping,
   - validates that the ticket id appears in docs/CODEX_SPRINT_TICKETS.md,
   - writes a helpful error and exits non-zero on any failure.
3) Add a small self-check mode if useful (e.g., `--verify <zip>` or `--list`) — optional, but it helps.
4) Update docs/CODEX_SPRINT_TICKETS.md:
   - Add Ticket-06b with the acceptance criteria above.
   - Add a short note marking the prior “ticket-06_checklist-final” bundle as FAIL due to missing run logs (process-only).
5) Update PROGRESS.md with a new entry for this run.

## Required run log (mandatory)
Set:
- RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-06b_bundle-integrity"

Create:
- docs/agent_runs/$RUN_NAME/
  - PROMPT.md (paste this entire prompt verbatim)
  - COMMANDS.md (every command you execute, in order)
  - RESULTS.md (what changed + how to verify + bundle path)
  - TESTS.md (tests you ran + outputs)
  - META.json (git sha before/after, branch, env notes)

## Minimal tests/commands to run (must log them)
- python3 -m compileall scripts/gpt_bundle.py
- make gpt-bundle TICKET=ticket-06b RUN_NAME=$RUN_NAME
- Verify contents:
  - python3 - << 'PY'
import zipfile, sys
z = zipfile.ZipFile(next(p for p in __import__("glob").glob("docs/gpt_bundles/*.zip")))
print("\n".join(z.namelist()))
PY

(If the repo already has a build dir and FAST tests are cheap, also run:
- ctest --test-dir build -L FAST --output-on-failure
…but this is optional for a bundler-only change; if you skip, state why in TESTS.md.)

## Commit policy (mandatory)
- Create branch: feature/ticket-06b_bundle-integrity
- Commit message: "ticket-06b: gpt-bundle completeness hard gate"
- Commit body MUST include:
  - Tests: <exact commands>
  - Bundle: <path to zip>
  - Run log: docs/agent_runs/$RUN_NAME/

## Generate the next review bundle (mandatory)
At the end, generate and record the path in RESULTS.md:
- make gpt-bundle TICKET=ticket-06b RUN_NAME=$RUN_NAME

## Suggested Codex invocation (safe)
Use sandbox + approvals:
- codex --sandbox workspace-write --ask-for-approval on-request

Full-autonomy mode is NOT requested; do not use yolo/no-approval modes.

## Human merge checklist (include at end of RESULTS.md)
- Bundle contains required run logs + diff + last commit
- Bundler fails fast on missing items
- Ticket-06b exists in docs/CODEX_SPRINT_TICKETS.md
- PROGRESS.md updated
- No secrets or raw WRDS data committed

You are Codex working on quant-pricer-cpp.

FIRST read these files (in this order) and treat them as binding:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-06c — Prove bundler hard-gate + clean the diff

Do NOT write a long upfront plan. Do the work.

## Goal
Make `make gpt-bundle` objectively audit-safe by (1) proving fail-fast behavior on missing inputs + missing ticket ids, (2) completing META.json provenance, and (3) removing unrelated/unsafe diffs from the bundle-plumbing work.

## Acceptance criteria (objective, must satisfy)
1) Logged negative tests prove:
   a) Bundling fails (exit code != 0) and prints a clear list of missing required files when any required item is absent.
   b) Bundling fails (exit code != 0) when the ticket id is NOT present in docs/CODEX_SPRINT_TICKETS.md.
2) META.json for this run has BOTH:
   - git_sha_before
   - git_sha_after (must equal HEAD after commit)
3) DIFF for this ticket does NOT include unrelated `artifacts/heston/**` churn:
   - revert any accidental changes from ticket-06b scope
   - if those files are license-risk, add/append a separate Ticket-07 instead of mixing here.
4) A new bundle is generated at the end and includes all required items.

## Implementation steps
1) Inspect:
   - scripts/gpt_bundle.py
   - Makefile (gpt-bundle target)
   - docs/CODEX_SPRINT_TICKETS.md (mark 06b FAIL; add 06c + optionally 07)
2) Implement/ensure in scripts/gpt_bundle.py:
   - a single source of truth `REQUIRED_PATHS` for the bundle
   - preflight checks that:
     - every required file exists BEFORE zipping
     - docs/CODEX_SPRINT_TICKETS.md contains the ticket id (string match on Ticket-06c or ticket-06c)
   - strong error messages that enumerate missing files
   - (optional but helpful) `--verify <zip>` mode that checks required members exist inside a zip (exit non-zero if missing)
3) Add an explicit self-test path (choose ONE):
   A) `python3 scripts/gpt_bundle.py --self-test` (preferred), OR
   B) `make gpt-bundle-selftest`
   Self-test must run the two negative tests from Acceptance #1 without permanently modifying the repo.
4) Revert unrelated changes:
   - inspect `git status` and `git diff`
   - if `artifacts/heston/**` changed as collateral, revert those hunks/files on this branch (do NOT force-push / rewrite history).
5) Update docs:
   - docs/CODEX_SPRINT_TICKETS.md: mark Ticket-06b FAIL; add Ticket-06c (and Ticket-07 if needed)
   - PROGRESS.md: add an entry for this run
6) Write full run logs under docs/agent_runs/<RUN_NAME>/.

## Run naming
RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-06c_bundle-hardgate-tests"

## Required run log folder (mandatory)
Create docs/agent_runs/$RUN_NAME/ containing:
- PROMPT.md (paste this entire prompt verbatim)
- COMMANDS.md (every command executed, in order)
- RESULTS.md (what changed + evidence; include outputs for negative tests)
- TESTS.md (self-test output + exit codes)
- META.json (include git_sha_before and git_sha_after)

## Minimal tests/commands to run (must be logged)
- python3 -m compileall scripts/gpt_bundle.py
- Run bundler self-test (or manual negative tests) and capture the stdout/stderr into TESTS.md:
  - missing-file case must show non-zero exit and list missing files
  - missing-ticket case must show non-zero exit and explain ticket not found
- Generate bundle:
  - make gpt-bundle TICKET=ticket-06c RUN_NAME=$RUN_NAME
- Verify contents:
  - python3 - << 'PY'
import zipfile, glob
zpath = sorted(glob.glob("docs/gpt_bundles/*ticket-06c*.zip"))[-1]
z = zipfile.ZipFile(zpath)
print("\n".join(z.namelist()))
PY

Real-data smoke is NOT required for a bundler-only ticket. If you do run any WRDS/sample commands anyway, log them.

## Commit policy (mandatory)
- Branch: feature/ticket-06c_bundle-hardgate-tests
- Commit message: "ticket-06c: prove gpt-bundle hard gate"
- Commit body MUST include:
  - Tests: <exact commands>
  - Bundle: <path>
  - Run log: docs/agent_runs/$RUN_NAME/

## Generate the next review bundle (mandatory)
At the end:
- make gpt-bundle TICKET=ticket-06c RUN_NAME=$RUN_NAME
Record the bundle path in RESULTS.md.

## Suggested Codex invocation (safe)
Use sandbox + approvals:
- codex --sandbox workspace-write --ask-for-approval on-request

Full-autonomy mode is NOT requested; do not use yolo/no-approval modes.

## Human merge checklist (include at end of RESULTS.md)
- [ ] Negative tests prove bundler fail-fast (missing files + missing ticket)
- [ ] META.json has git_sha_after populated and equals HEAD
- [ ] No secrets / no raw or quote-level WRDS surfaces committed
- [ ] Diff scope limited to bundler + docs (no unrelated artifact churn)
- [ ] Bundle contains required items (run logs + DIFF.patch + LAST_COMMIT.txt)

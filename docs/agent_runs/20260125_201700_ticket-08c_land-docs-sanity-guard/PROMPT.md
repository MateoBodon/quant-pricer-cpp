# Prompt

Ticket: ticket-08c_land-docs-sanity-guard

Goal: land ticket-08b cleanly with docs sanity guard + runbooks/backlog/runlog, keep
artifacts untouched, and ensure FAST tests pass.

Constraints:
- Revert docs/artifacts/manifest.json + metrics_summary.{md,json} to match main (no refresh).
- Keep docs_sanity_fast registration in CMakeLists.txt and PROGRESS.md cleanup.
- Add/track/commit tests/test_docs_sanity_fast.py, docs/RUNBOOK.md,
  project_state/RUNBOOK.md, project_state/BACKLOG.md, and the ticket-08b run log folder.
- Do not add unrelated new directories (docs/tickets/, tools/agentic/) in this ticket.
- End with clean git status and FAST tests passing.

Required steps:
- Confirm Agentic System scaffold (AGENTS.md, PROJECT.md, tools/agentic/).
- Create docs/tickets/ticket-08c_land-docs-sanity-guard.md (Goal/Scope/Acceptance/Plan/Notes).
- Run build + FAST tests (CMake + ctest) and docs_sanity_fast.
- Update PROGRESS.md.
- Emit a GPT bundle using the gpt-bundle skill (repo-local script preferred).

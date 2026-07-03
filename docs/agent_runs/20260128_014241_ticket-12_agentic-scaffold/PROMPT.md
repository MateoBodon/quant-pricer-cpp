# Prompt

Ticket: **ticket-12**
Run: **20260128_014241_ticket-12_agentic-scaffold**
Summary: Track agentic kit scaffolding + ignore .agent

## Goal
- [x] Track the untracked agentic-kit docs/scripts and ignore `.agent/` scratch output.

## Constraints
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [x] No secrets in repo or logs
- [x] Tests run (or explicitly marked N/A)

## Plan
1. Add `.agent/` to `.gitignore` to keep scratch output out of git.
2. Track the untracked agentic-kit docs/scripts and prior run log.
3. Update PROGRESS.md and fill this run log.

## Files to touch (expected)
- .gitignore
- docs/NOW.md
- docs/TICKETS.md
- docs/agent_runs/20260127_024443_ticket-00_agentic-kit-setup/
- tools/agentic/runlog_init.py
- tools/agentic/ticket_new.py
- tools/agentic/validate_runlog.py
- docs/agent_runs/20260128_014241_ticket-12_agentic-scaffold/
- PROGRESS.md

## Definition of Done
- [x] Acceptance criteria met
- [x] PROGRESS.md updated
- [x] Run log filled (RESULTS/TESTS)

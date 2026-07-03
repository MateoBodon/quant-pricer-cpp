# Prompt

Ticket: **ticket-12**
Run: **20260127_210235_ticket-ticket-12**
Summary: Track ticket-12 deliverables and regenerate GPT bundle

## Goal
- [x] Ticket-12 deliverables are staged/tracked and a fresh GPT bundle exists with a non-empty staged patch.

## Constraints
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [x] No secrets in repo or logs
- [x] Tests run (or explicitly marked N/A)

## Plan
1. Stage the script, FAST test, and prior run log for ticket-12.
2. Regenerate the GPT bundle with the staged patch.
3. Update PROGRESS.md and fill this run log.

## Files to touch (expected)
- PROGRESS.md
- scripts/reproduce_wrds_local_metrics.sh
- tests/test_wrds_local_metrics_one_command_fast.py
- docs/agent_runs/20260127_043553_ticket-12_wrds-local-metrics/
- docs/agent_runs/20260127_210235_ticket-ticket-12/

## Definition of Done
- [x] Acceptance criteria met
- [x] PROGRESS.md updated
- [x] Run log filled (RESULTS/TESTS)

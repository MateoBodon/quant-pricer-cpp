# Prompt

Ticket: **ticket-12**
Run: **20260212_225813_ticket-12_bundle-evidence-repair**
Summary: Repair ticket-12 review bundle evidence (base..HEAD diff + snapshot + runlog inclusion)

## Goal
- [x] Produce a ticket-12 bundle with non-empty `base..HEAD` diff evidence, refreshed snapshot metadata, and embedded run-log files.

## Constraints
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [x] No secrets in repo or logs
- [x] Tests run (or explicitly marked N/A)

## Plan
1. Patch `tools/agentic/gpt_bundle.py` to emit `DIFF.patch` (`base..HEAD`), refresh snapshot every run, and include run logs via `--run-name`.
2. Generate a repaired ticket-12 bundle and verify required evidence files.
3. Record the run in `PROGRESS.md` and finalize this run log.

## Files to touch (expected)
- `tools/agentic/gpt_bundle.py`
- `docs/_generated/repo_snapshot.md`
- `docs/agent_runs/20260212_225813_ticket-12_bundle-evidence-repair/`
- `PROGRESS.md`
- `artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip`

## Definition of Done
- [x] Acceptance criteria met
- [x] PROGRESS.md updated
- [x] Run log filled (RESULTS/TESTS)

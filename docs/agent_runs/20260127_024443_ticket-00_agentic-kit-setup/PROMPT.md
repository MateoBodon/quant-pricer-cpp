# Prompt

Ticket: **ticket-00**
Run: **20260127_024443_ticket-00_agentic-kit-setup**
Summary: Agentic System Kit v2 refresh

## Goal
- [x] Refresh Agentic System Kit tooling, verify tracking structure, and generate a project-state bundle with the path recorded in PROGRESS.md.

## Constraints
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [x] Do not overwrite existing AGENTS.md/PROJECT.md/PROGRESS.md contents (only append updates)
- [x] docs/agent_runs/ remains tracked (not ignored)
- [x] No secrets in repo or logs
- [x] Tests run (or explicitly marked N/A)

## Plan
1. Run repo bootstrap in tools-only mode.
2. Verify .gitignore contains the Agentic System Kit block and does not ignore docs/agent_runs.
3. Generate the project-state bundle and record its path in PROGRESS.md.

## Files to touch (expected)
- .gitignore
- tools/agentic/README.md
- tools/agentic/gpt_bundle.py
- tools/agentic/project_state_refresh.py
- tools/agentic/repo_snapshot.py
- project_state/_generated/import_graph.json
- project_state/_generated/make_targets.txt
- project_state/_generated/repo_inventory.json
- project_state/_generated/symbol_index.json
- PROGRESS.md
- docs/agent_runs/20260127_024443_ticket-00_agentic-kit-setup/*

## Definition of Done
- [x] Acceptance criteria met
- [x] PROGRESS.md updated
- [x] Run log filled (RESULTS/TESTS)

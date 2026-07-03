# Commands

Log commands that materially change state or produce results.

- (2026-01-28) git switch -c codex/ticket-12-wrds-local-metrics
- (2026-01-28) python3 tools/agentic/runlog_init.py --ticket "ticket-12" --summary "Finalize ticket-12 staging + bundle regeneration"
  - created docs/agent_runs/20260128_000449_ticket-ticket-12
- (2026-01-28) git restore --staged docs/agent_runs/20260127_210235_ticket-ticket-12
- (2026-01-28) git add CHANGELOG.md CMakeLists.txt docs/RUNBOOK.md
- (2026-01-28) git add docs/agent_runs/20260127_210235_ticket-ticket-12
- (2026-01-28) apply_patch (PROGRESS.md)
  - aligned bundle path with run log
- (2026-01-28) git add PROGRESS.md
- (2026-01-28) git commit -m "ticket-12: complete wrds local metrics deliverables"
- (2026-01-28) python3 tools/agentic/gpt_bundle.py --ticket "ticket-12" --run-name "20260128_000449_ticket-ticket-12"
  - wrote artifacts/_local/gpt_bundles/gpt_bundle_20260128_000746_ticket-ticket-12.zip

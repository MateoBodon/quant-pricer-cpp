# Commands

Log commands that materially change state or produce results.

- (2026-01-28) python3 tools/agentic/runlog_init.py --ticket "ticket-12" --summary "Track agentic kit scaffolding + ignore .agent" --run-name "20260128_014241_ticket-12_agentic-scaffold"
  - created docs/agent_runs/20260128_014241_ticket-12_agentic-scaffold
- (2026-01-28) apply_patch (.gitignore)
  - ignore .agent/ scratch output
- (2026-01-28) cat > docs/agent_runs/20260128_014241_ticket-12_agentic-scaffold/PROMPT.md
  - filled prompt checklist and plan
- (2026-01-28) apply_patch (PROGRESS.md)
  - recorded agentic-kit scaffolding tracking
- (2026-01-28) git add .gitignore PROGRESS.md docs/NOW.md docs/TICKETS.md docs/agent_runs/20260127_024443_ticket-00_agentic-kit-setup docs/agent_runs/20260128_014241_ticket-12_agentic-scaffold tools/agentic/runlog_init.py tools/agentic/ticket_new.py tools/agentic/validate_runlog.py
- (2026-01-28) git commit -m "ticket-12: track agentic kit scaffolding"

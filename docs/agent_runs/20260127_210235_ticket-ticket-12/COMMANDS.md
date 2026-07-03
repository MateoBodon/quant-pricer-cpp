# Commands

Log commands that materially change state or produce results.

- (2026-01-27) python3 tools/agentic/runlog_init.py --ticket "ticket-12" --summary "Track ticket-12 deliverables and regenerate GPT bundle"
  - created docs/agent_runs/20260127_210235_ticket-ticket-12
- (2026-01-27) git add scripts/reproduce_wrds_local_metrics.sh tests/test_wrds_local_metrics_one_command_fast.py docs/agent_runs/20260127_043553_ticket-12_wrds-local-metrics/
  - staged ticket-12 deliverables
- (2026-01-27) python3 tools/agentic/gpt_bundle.py --ticket "ticket-12_wrds-local-metrics" --run-name "20260127_043553_ticket-12_wrds-local-metrics"
  - wrote artifacts/_local/gpt_bundles/gpt_bundle_20260127_210313_ticket-ticket-12-wrds-local-metrics.zip
- (2026-01-27) python3 tools/agentic/gpt_bundle.py --ticket "ticket-12_wrds-local-metrics" --run-name "20260127_043553_ticket-12_wrds-local-metrics"
  - wrote artifacts/_local/gpt_bundles/gpt_bundle_20260127_213237_ticket-ticket-12-wrds-local-metrics.zip
- (2026-01-27) apply_patch (PROGRESS.md)
  - recorded tracking + bundle note for ticket-12
- (2026-01-27) git add PROGRESS.md docs/agent_runs/20260127_210235_ticket-ticket-12/
  - staged this run log + progress update
- (2026-01-27) apply_patch (docs/agent_runs/20260127_210235_ticket-ticket-12/PROMPT.md)
  - filled prompt checklist and plan
- (2026-01-27) git add docs/agent_runs/20260127_210235_ticket-ticket-12/PROMPT.md
  - staged updated run prompt

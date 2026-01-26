# Prompt

Ticket: ticket-10c_tracking-policy-wrds-local

Goal: Make the WRDS local-metrics workflow TRACKING_POLICY-compliant and finish ticket-10b by tracking the missing run log + ticket docs while keeping docs/artifacts clean.

Constraints:
- Update local WRDS outputs to `artifacts/_local` (not `docs/artifacts/wrds_local`).
- Ensure local manifests/provenance write to scratch.
- Update `docs/RUNBOOK.md` + ticket-10b docs to match.
- Track `docs/agent_runs/20260126_040139_ticket-10b_generate-realdata-metrics` and the ticket-10b ticket files.
- Do not commit raw/derived WRDS outputs.
- Run the provided FAST test command and generate a GPT bundle.

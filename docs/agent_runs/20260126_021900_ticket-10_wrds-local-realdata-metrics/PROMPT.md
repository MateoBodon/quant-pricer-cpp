# Prompt

Ticket: ticket-10_wrds-local-realdata-metrics

Goal: Export license-safe real-data WRDS metrics (local cache) for resume updates, with provenance, without committing raw data.

Constraints:
- Add scripts/wrds_realdata_metrics_export.py for sanitized JSON/MD export.
- Ensure WRDS outputs can target gitignored docs/artifacts/wrds_local (use --output-root if needed).
- Add FAST test for exporter schema and restricted-field guard.
- Update docs/RUNBOOK.md with AX162-S sample/local commands.
- Run provided test command end-to-end.

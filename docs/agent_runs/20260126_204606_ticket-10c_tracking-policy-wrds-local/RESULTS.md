# Results

- Kept WRDS local defaults and provenance in `artifacts/_local/wrds_local` and removed the legacy docs/artifacts local ignore; local runs avoid mutating `docs/artifacts/manifest.json` by default.
- Updated WRDS guidance and tickets to reference `artifacts/_local` (README, RUNBOOK, WRDS_Results, KNOWN_ISSUES, ticket-10* docs) and refreshed PROGRESS/DECISIONS language.
- Tracked the WRDS real-data exporter + FAST test registration (`scripts/wrds_realdata_metrics_export.py`, `tests/test_wrds_realdata_export_fast.py`, `CMakeLists.txt`).
- Confirmed ticket-10b run log + dateset clone are tracked and staged ticket-10b ticket files.
- Restored `docs/artifacts/manifest.json` after FAST tests to keep tracked artifacts clean.
- GPT bundle: `artifacts/_local/gpt_bundles/gpt_bundle_20260126_221408_ticket-10c_tracking-policy-wrds-local.zip`.

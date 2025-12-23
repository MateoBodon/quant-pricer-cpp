# Results

- Added as-of correctness gates: calibration now enforces `quote_date == trade_date`, OOS evaluation enforces `quote_date == next_trade_date` (via `oos_pricing.evaluate`), and the pipeline writes trade_date/next_trade_date into `wrds_heston` manifest entries.
- Introduced `WRDS_SAMPLE_PATH` override plus two poison sample fixtures and a FAST test that confirms the pipeline fails-closed on as-of mismatches (explicitly re-run).
- Verified sample pipeline run wrote outputs under `docs/artifacts/wrds/`.
- Artifacts updated by FAST + sample pipeline runs: `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.md`, `docs/artifacts/metrics_summary.json`.
- Bundle: `docs/gpt_bundles/20251223T193039Z_ticket-02_20251223_183500_ticket-02_wrds-asof-checks.zip`.
- Pre-fix poison failure was not captured; the new poison test demonstrates fail-closed behavior after the change.

Human merge checklist
- Poison-pill test fails without the fix and fails-closed in production paths
- Sample pipeline smoke ran successfully in WRDS_USE_SAMPLE=1 mode
- No raw WRDS extracts or credentials committed or printed
- PROGRESS.md updated; KNOWN_ISSUES/CONFIG_REFERENCE updated if impacted
- Bundle generated via make gpt-bundle and contains complete non-empty run logs

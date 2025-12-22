# Results

- Hardened `scripts/gpt_bundle.py` to require all bundle inputs (including run log files) and ticket presence before zipping; added `--verify` to check bundle contents.
- Added Ticket-06b to `docs/CODEX_SPRINT_TICKETS.md` and recorded the prior `ticket-06_checklist-final` bundle as FAIL due to missing run logs (process-only).
- Updated `PROGRESS.md` for this run.
- Generated GPT bundle: `docs/gpt_bundles/20251222T015729Z_ticket-06b_20251222_014941_ticket-06b_bundle-integrity.zip`.
- Verified bundle contents via `unzip -l` (includes required run log files).
- Sanity check: temporarily removed `PROGRESS.md` and confirmed `scripts/gpt_bundle.py` exited non-zero with a missing-file error.
- Secrets scan: hits limited to documentation/env references; no secrets committed.
- Raw market-data scan: hits limited to scripts/docs, sample data (`wrds_pipeline/sample_data/spx_options_sample.csv`), and derived Heston fit CSVs under `artifacts/heston/`; no raw quote surfaces committed.

## Verification (executed)
- `python3 -m compileall scripts/gpt_bundle.py`
- `make gpt-bundle TICKET=ticket-06b RUN_NAME=20251222_014941_ticket-06b_bundle-integrity TIMESTAMP=20251222T015729Z`
- `unzip -l docs/gpt_bundles/*ticket-06b*.zip`
- `python3 scripts/gpt_bundle.py --ticket ticket-06b --run-name 20251222_014941_ticket-06b_bundle-integrity --timestamp 20251222T015729Z` (with `PROGRESS.md` temporarily moved; expected failure)
- `rg -n "WRDS_PASSWORD|WRDS_USERNAME|password|token|secret" -S .`
- `rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S .`

## Notes
- FAST tests skipped (bundler-only change; build dir not validated in this run).
- Sources consulted: none.

## Human merge checklist
- [x] Bundle contains required run logs + diff + last commit
- [x] Bundler fails fast on missing items
- [x] Ticket-06b exists in docs/CODEX_SPRINT_TICKETS.md
- [x] PROGRESS.md updated
- [x] No secrets or raw WRDS data committed

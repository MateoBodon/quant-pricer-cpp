# Results

## Summary
- Added a single REQUIRED_PATHS source of truth plus a `--self-test` hard-gate in `scripts/gpt_bundle.py` for missing required files and missing ticket ids.
- Marked Ticket-06b as FAIL, added Ticket-06c, and logged the run in `PROGRESS.md`.
- Reverted unrelated `artifacts/heston/**` churn from the branch.

## Evidence: negative tests (from self-test)
```
[gpt-bundle][self-test] missing-file exit code: 1
[gpt-bundle] missing required items:
  - docs/agent_runs/_gpt_bundle_selftest_39fffb3d_missing/PROMPT.md
  - docs/agent_runs/_gpt_bundle_selftest_39fffb3d_missing/COMMANDS.md
  - docs/agent_runs/_gpt_bundle_selftest_39fffb3d_missing/RESULTS.md
  - docs/agent_runs/_gpt_bundle_selftest_39fffb3d_missing/TESTS.md
  - docs/agent_runs/_gpt_bundle_selftest_39fffb3d_missing/META.json
[gpt-bundle][self-test] missing-ticket exit code: 1
[gpt-bundle] ticket id not found in docs/CODEX_SPRINT_TICKETS.md: ticket-does-not-exist
[gpt-bundle] self-test passed
```

## Bundle
- Path: `docs/gpt_bundles/20251222T033950Z_ticket-06c_20251222_032810_ticket-06c_bundle-hardgate-tests.zip`
- Verified contents:
```
AGENTS.md
docs/PLAN_OF_RECORD.md
docs/DOCS_AND_LOGGING_SYSTEM.md
docs/CODEX_SPRINT_TICKETS.md
PROGRESS.md
project_state/CURRENT_RESULTS.md
project_state/KNOWN_ISSUES.md
project_state/CONFIG_REFERENCE.md
docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/PROMPT.md
docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/COMMANDS.md
docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/RESULTS.md
docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/TESTS.md
docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/META.json
DIFF.patch
LAST_COMMIT.txt
```
- Bundle verify (`python3 scripts/gpt_bundle.py --verify ...`) output:
```
[gpt-bundle] bundle verification passed: docs/gpt_bundles/20251222T033950Z_ticket-06c_20251222_032810_ticket-06c_bundle-hardgate-tests.zip
```

## Scans
### Secret scan (rg -n "WRDS_PASSWORD|WRDS_USERNAME|password|token|secret" -S .)
- Hits are limited to documentation references, code tokens/identifiers, and prior run logs; no credentials or secret values were found.
- Notable paths include: `docs/Results.md`, `project_state/CONFIG_REFERENCE.md`, `wrds_pipeline/ingest_sppx_surface.py`, `src/main.cpp`, and prior run logs.

### Quote-surface scan (rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S .)
- Hits include WRDS pipeline code references (`wrds_pipeline/ingest_sppx_surface.py`), the deterministic sample data (`wrds_pipeline/sample_data/spx_options_sample.csv`), and pre-existing Heston fit artifacts under `artifacts/heston/`.
- No new quote-surface files were added or modified in this ticket; `artifacts/heston/**` churn was reverted.
 
### Acceptance
- User accepted scan hits as pre-existing doc/code references and approved proceeding without removal.

## Notes
- Initial `--self-test` failed due to an over-escaped ticket regex; fixed and reran.
- Pre-existing working-tree edits to `AGENTS.md` and `Makefile` were left untouched; the bundle diff excludes `artifacts/heston/**` churn.

## Human merge checklist
- [x] Negative tests prove bundler fail-fast (missing files + missing ticket)
- [x] META.json has git_sha_after populated and equals HEAD
- [x] No secrets / no raw or quote-level WRDS surfaces committed (accepted scan hits)
- [x] Diff scope limited to bundler + docs (no unrelated artifact churn)
- [x] Bundle contains required items (run logs + DIFF.patch + LAST_COMMIT.txt)

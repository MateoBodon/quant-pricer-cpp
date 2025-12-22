# Results

## Changes
- Added `scripts/check_data_policy.py` to scan git-tracked data/artifact files for restricted patterns (handles spaces via `git ls-files -z`).
- Added FAST guard test `tests/test_data_policy_fast.py` and CTest registration.
- Removed tracked Heston fit CSVs containing `strike/market_iv` surfaces.
- Sanitized WRDS sample CSV headers (`best_bid/best_offer` → `bid/ask`) and mapped both header styles in `_load_sample`.
- Documented Heston fit-table policy in `artifacts/heston/README.md`, added Ticket-07 entry to `docs/CODEX_SPRINT_TICKETS.md`, and updated `AGENTS.md`, `PROGRESS.md`, `project_state/KNOWN_ISSUES.md`.

## Scan outputs
Before (from `git ls-files | xargs rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S`):
```
rg: ROADMAP: No such file or directory (os error 2)
rg: (1).md: No such file or directory (os error 2)
artifacts/heston/series_runs/fit_20230601.csv
1:strike,ttm,market_iv,model_iv,abs_error

artifacts/heston/fit_20240614.csv
1:strike,ttm,market_iv,model_iv,abs_error

artifacts/heston/fit_20230601.csv
1:strike,ttm,market_iv,model_iv,abs_error

artifacts/heston/series_runs/fit_20240614.csv
1:strike,ttm,market_iv,model_iv,abs_error

wrds_pipeline/sample_data/spx_options_sample.csv
1:trade_date,exdate,cp_flag,strike_price,best_bid,best_offer,spot,rate,dividend,forward_price
```

After (`python3 scripts/check_data_policy.py`):
```
[data-policy] OK: no restricted patterns found in tracked data artifacts.
```

## Removed/changed paths
- Removed:
  - `artifacts/heston/fit_20230601.csv`
  - `artifacts/heston/fit_20240614.csv`
  - `artifacts/heston/series_runs/fit_20230601.csv`
  - `artifacts/heston/series_runs/fit_20240614.csv`
- Added:
  - `scripts/check_data_policy.py`
  - `tests/test_data_policy_fast.py`
  - `artifacts/heston/README.md`
- Updated:
  - `wrds_pipeline/sample_data/spx_options_sample.csv`
  - `wrds_pipeline/ingest_sppx_surface.py`
  - `CMakeLists.txt`
  - `AGENTS.md`
  - `docs/CODEX_SPRINT_TICKETS.md`
  - `project_state/KNOWN_ISSUES.md`
  - `PROGRESS.md`

## Bundle
- Bundle: `docs/gpt_bundles/20251222T170132Z_ticket-07_20251222_044808_ticket-07_data-policy-guard.zip`
- Verified: `python3 scripts/gpt_bundle.py --verify` passed.

## Checklist notes
- `git ls-files | xargs rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S` reports only code/docs (and a path split on `ROADMAP (1).md`); no tracked data artifacts matched.
- `git ls-files -z -- artifacts docs/artifacts data wrds_pipeline/sample_data | xargs -0 rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S` produced no matches (rg exit 1 when empty).
- Secret scan hits limited to documentation/env references and code tokens; no credentials or secret values committed.

## Human merge checklist
- [ ] No tracked quote-surface artifacts remain (scan is clean)
- [ ] data policy guard script exists and passes
- [ ] FAST tests pass (if run)
- [ ] PROGRESS + project_state docs updated
- [ ] Bundle generated and contains required run logs + DIFF.patch + LAST_COMMIT.txt

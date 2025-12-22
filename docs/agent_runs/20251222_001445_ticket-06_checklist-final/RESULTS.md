# Results

- Added `.agent/` to `.gitignore`, plus a `gpt-bundle` Makefile target backed by `scripts/gpt_bundle.py`.
- Regenerated sample-mode artifacts via `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`, updating `docs/artifacts/` (benchmarks, QMC vs PRNG, QL parity, metrics summary, manifest) and removing stale slow-test logs.
- Verified metrics snapshot shows WRDS as a “sample bundle” and confirmed no absolute paths in `docs/artifacts/metrics_summary.*` or `docs/artifacts/manifest.json`.
- WRDS sample pipeline succeeded with `python3` (`source_today=sample` / `source_next=sample`); the exact `python` command failed because `python` is not on PATH.
- Updated `project_state/CURRENT_RESULTS.md` and `project_state/KNOWN_ISSUES.md` (license/provenance audit note for Heston fit CSVs).
- Generated GPT bundle: `docs/gpt_bundles/20251222T002413Z_ticket-06_20251222_001445_ticket-06_checklist-final.zip`.

## Artifacts
- `docs/artifacts/metrics_summary.md`
- `docs/artifacts/metrics_summary.json`
- `docs/artifacts/manifest.json`
- `docs/validation_pack.zip` (generated, ignored)
- `docs/artifacts/bench/*`
- `docs/artifacts/ql_parity/*`
- `docs/artifacts/qmc_vs_prng_equal_time.*`
- `docs/gpt_bundles/20251222T002413Z_ticket-06_20251222_001445_ticket-06_checklist-final.zip`

## Checks
- Secrets scan: only documentation/environment references; no secrets committed.
- Raw data scan: hits limited to sample data + existing Heston fit CSVs; no WRDS raw quote surfaces under committed `docs/artifacts/`.

## Notes
- FAST tests failed due to missing matplotlib (see TESTS.md).
- Sources consulted: none.

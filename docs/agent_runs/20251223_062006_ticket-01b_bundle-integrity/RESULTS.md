# Results

- Updated `scripts/gpt_bundle.py` to hard-gate empty run logs (min-size check), add `--base-sha`/`BASE_SHA` support, and bundle base-range diffs plus a short commit log (`COMMITS.txt`).
- Marked ticket-01 as **FAIL** (missing evidence) and added ticket-01b to `docs/CODEX_SPRINT_TICKETS.md`; updated `PROGRESS.md` and `CHANGELOG.md`.
- Bundles created:
  - `docs/gpt_bundles/20251223T063041Z_ticket-01_20251222_204744_ticket-01_unify-artifacts.zip` (BASE_SHA=cf1d770d18d26b8db15c0638c692ac50f5f2747e; implementation run log).
  - `docs/gpt_bundles/20251223T063041Z_ticket-01b_20251223_062006_ticket-01b_bundle-integrity.zip` (this run; re-run after finalizing logs).
- Note: an earlier ticket-01 bundle at `docs/gpt_bundles/20251223T062645Z_ticket-01_20251222_204744_ticket-01_unify-artifacts.zip` was superseded by the timestamped bundle above.

Human merge checklist:
- Bundle fails on empty run logs
- New ticket-01 bundle includes the implementation run log + a DIFF.patch with scripts/tests changes
- No secrets or raw WRDS data were committed
- PROGRESS + sprint tickets updated

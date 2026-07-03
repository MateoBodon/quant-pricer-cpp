# Commands

Log commands that materially change state or produce results.

- (2026-02-12) `python3 tools/agentic/runlog_init.py --run-name 20260212_225813_ticket-12_bundle-evidence-repair --ticket ticket-12 --summary "Repair ticket-12 review bundle evidence (base..HEAD diff + snapshot + runlog inclusion)"`
  - Created `docs/agent_runs/20260212_225813_ticket-12_bundle-evidence-repair/`.
- (2026-02-12) `apply_patch` (update `tools/agentic/gpt_bundle.py`)
  - Added commit-range diff evidence (`DIFF.patch`/`COMMITS.txt`), forced snapshot refresh, and run-log inclusion via `--run-name`.
- (2026-02-12) `python3 -m compileall tools/agentic/gpt_bundle.py`
  - Passed.
- (2026-02-12) `python3 tools/agentic/gpt_bundle.py --ticket ticket-12 --run-name 20260128_005626_ticket-ticket-12 --base-ref main`
  - Wrote `artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip` with base SHA `0318d95d12a947cef2fde2d8932fffd969998bb5`.
- (2026-02-12) Bundle validation commands:
  - `unzip -l artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip`
  - `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip changed_files.txt`
  - `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip docs/_generated/repo_snapshot.md | sed -n '1,40p'`
  - `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip DIFF.patch | rg -n "scripts/reproduce_wrds_local_metrics\\.sh|tests/test_wrds_local_metrics_one_command_fast\\.py|docs/RUNBOOK\\.md|CMakeLists\\.txt|PROGRESS\\.md|docs/agent_runs/20260128_005626_ticket-ticket-12"`
  - Verified required evidence is present and non-empty (`DIFF.patch`, `git_diff.patch`, `git_diff_stat.txt`, refreshed snapshot, run-log files).
- (2026-02-12) `git add tools/agentic/runlog_init.py && git commit -m "chore: make runlog_init idempotent for existing run-name" -m "Tests: not run (small Python control-flow change only)" -m "Artifacts: none"`
  - Created commit `a98fb5f` as a separate idempotent re-run fix.
- (2026-02-12) `git add PROGRESS.md tools/agentic/gpt_bundle.py docs/agent_runs/20260212_225813_ticket-12_bundle-evidence-repair && git commit -m "ticket-12: repair bundle evidence packaging" ...`
  - Finalized bundle-repair changes in a second, separate commit.

# Results

## Summary
- Repaired `tools/agentic/gpt_bundle.py` so bundles now carry reviewable commit-range evidence (`DIFF.patch` + `COMMITS.txt`) using `base..HEAD` instead of only dirty-tree diff files.
- Fixed snapshot drift by refreshing `docs/_generated/repo_snapshot.md` on each bundle run (no stale host/path/HEAD metadata).
- Added run-log inclusion support (`--run-name`) and verified `docs/agent_runs/20260128_005626_ticket-ticket-12/PROMPT.md`, `docs/agent_runs/20260128_005626_ticket-ticket-12/COMMANDS.md`, `docs/agent_runs/20260128_005626_ticket-ticket-12/RESULTS.md`, `docs/agent_runs/20260128_005626_ticket-ticket-12/TESTS.md`, and `docs/agent_runs/20260128_005626_ticket-ticket-12/META.json` are inside the new bundle.
- Regenerated ticket-12 bundle with non-empty diff evidence and required ticket files listed in `changed_files.txt` (including `scripts/reproduce_wrds_local_metrics.sh`, `tests/test_wrds_local_metrics_one_command_fast.py`, `docs/RUNBOOK.md`, `CMakeLists.txt`, `PROGRESS.md`).

## Key outputs
- `artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip`
- `tools/agentic/gpt_bundle.py`
- `docs/_generated/repo_snapshot.md`

## Notes
- `git_diff_cached.patch` can remain empty when there are no staged changes; canonical review evidence now lives in `DIFF.patch` and `COMMITS.txt`.
- Commits split per user instruction:
  - `a98fb5f` `chore: make runlog_init idempotent for existing run-name` (runlog idempotency fix only)
  - `ticket-12: repair bundle evidence packaging` (bundle-repair and run-log/progress updates)

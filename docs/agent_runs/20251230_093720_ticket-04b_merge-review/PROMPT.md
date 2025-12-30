review checklist, after, commit changes, merge to main, push to origin, then tell me final correct bundle to upload to gpt.  checklist: For merging the ticket-04b branch:

Verify scripts/gpt_bundle.py now fails on empty diff range unless --allow-empty-diff is passed (behavior visible in docs/agent_runs/20251226_065320_ticket-04b_bundle-diff-repair/TESTS.md).

Confirm FAST includes the new guard test:

gpt_bundle_empty_diff_fast is registered in CMakeLists.txt and runs under ctest -L FAST. (See DIFF.patch + TESTS.md.)

Confirm PROGRESS.md and docs/CODEX_SPRINT_TICKETS.md updates match the implemented behavior and bundle paths.

Sanity-check no secrets/raw data in diffs/logs (DIFF.patch + run logs contain only pattern-scan commands, not credentials).

---

review checklist, after, commit changes, merge to main, push to origin, then tell me final correct bundle to upload to gpt.  checklist: For
  merging the ticket-04b branch:

  Verify scripts/gpt_bundle.py now fails on empty diff range unless --allow-empty-diff is passed (behavior visible in docs/
  agent_runs/20251226_065320_ticket-04b_bundle-diff-repair/TESTS.md).

  Confirm FAST includes the new guard test:

  gpt_bundle_empty_diff_fast is registered in CMakeLists.txt and runs under ctest -L FAST. (See DIFF.patch + TESTS.md.)

  Confirm PROGRESS.md and docs/CODEX_SPRINT_TICKETS.md updates match the implemented behavior and bundle paths.

  Sanity-check no secrets/raw data in diffs/logs (DIFF.patch + run logs contain only pattern-scan commands, not credentials).

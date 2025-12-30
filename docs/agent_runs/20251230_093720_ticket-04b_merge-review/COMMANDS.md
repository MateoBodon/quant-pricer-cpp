1. RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-04b_merge-review"; RUN_DIR="docs/agent_runs/${RUN_NAME}"; mkdir -p "$RUN_DIR"; touch "$RUN_DIR/PROMPT.md" "$RUN_DIR/COMMANDS.md" "$RUN_DIR/RESULTS.md" "$RUN_DIR/TESTS.md" "$RUN_DIR/META.json"; echo "$RUN_NAME" # create run log files
2. cat <<'EOF' > docs/agent_runs/20251230_093720_ticket-04b_merge-review/PROMPT.md # record prompt
3. git status --short # check working tree
4. git branch --list 'codex/ticket-04b*' # locate ticket-04b branch
5. git switch codex/ticket-04b-bundle-diff-repair # switch to ticket-04b branch
6. sed -n '1,200p' docs/agent_runs/20251226_065320_ticket-04b_bundle-diff-repair/TESTS.md # verify empty diff failure
7. rg -n "gpt_bundle_empty_diff_fast" CMakeLists.txt # verify FAST guard test registered
8. rg -n "ticket-04b" PROGRESS.md docs/CODEX_SPRINT_TICKETS.md # locate doc updates
9. sed -n '180,240p' docs/CODEX_SPRINT_TICKETS.md # inspect ticket-04b section
10. ls docs/gpt_bundles/*ticket-04b* # list ticket-04b bundles
11. unzip -p docs/gpt_bundles/20251226T082814Z_ticket-04b_20251226_065320_ticket-04b_bundle-diff-repair.zip DIFF.patch | head -n 120 # inspect diff patch header
12. unzip -p docs/gpt_bundles/20251226T082814Z_ticket-04b_20251226_065320_ticket-04b_bundle-diff-repair.zip DIFF.patch | rg -n -i "password|passwd|secret|token|apikey|api_key|access_key|private_key|username|user=|login" # scan diff for secrets
13. rg -n -i "password|passwd|secret|token|apikey|api_key|access_key|private_key|username|user=|login" docs/agent_runs/20251226_065320_ticket-04b_bundle-diff-repair # scan run logs for secrets
14. sed -n '50,80p' PROGRESS.md # inspect PROGRESS entry for ticket-04b
15. cat <<'EOF' >> PROGRESS.md # append 2025-12-30 review entry
16. cat <<'EOF' > docs/agent_runs/20251230_093720_ticket-04b_merge-review/TESTS.md # write tests log
17. cat <<'EOF' > docs/agent_runs/20251230_093720_ticket-04b_merge-review/RESULTS.md # write results log
18. date -u +%Y-%m-%dT%H:%M:%SZ # capture finished_at_utc
19. cat <<'EOF' > docs/agent_runs/20251230_093720_ticket-04b_merge-review/META.json # write run metadata

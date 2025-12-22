# Tests

## python3 -m compileall scripts/gpt_bundle.py (exit 0)
Compiling 'scripts/gpt_bundle.py'...

## python3 scripts/gpt_bundle.py --self-test (exit 2, initial)
[gpt-bundle] self-test failed: no ticket id found in docs/CODEX_SPRINT_TICKETS.md

## python3 scripts/gpt_bundle.py --self-test (exit 0, after fix)
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

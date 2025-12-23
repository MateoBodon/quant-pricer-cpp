# Tests

## python3 -m compileall scripts/gpt_bundle.py (exit 0)
Compiling 'scripts/gpt_bundle.py'...

## make gpt-bundle TICKET=ticket-01b RUN_NAME=_gpt_bundle_emptytest_20251223_062606 (expected fail)
[gpt-bundle] run log files missing content:
  - docs/agent_runs/_gpt_bundle_emptytest_20251223_062606/PROMPT.md (0 bytes < 20)
  - docs/agent_runs/_gpt_bundle_emptytest_20251223_062606/COMMANDS.md (0 bytes < 20)
  - docs/agent_runs/_gpt_bundle_emptytest_20251223_062606/RESULTS.md (0 bytes < 20)
  - docs/agent_runs/_gpt_bundle_emptytest_20251223_062606/TESTS.md (0 bytes < 20)
  - docs/agent_runs/_gpt_bundle_emptytest_20251223_062606/META.json (0 bytes < 20)
make: *** [gpt-bundle] Error 1
exit=2

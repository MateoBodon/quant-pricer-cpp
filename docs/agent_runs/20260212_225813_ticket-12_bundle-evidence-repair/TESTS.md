# Tests

- [x] `python3 -m compileall tools/agentic/gpt_bundle.py`
  - Result: passed (`Compiling 'tools/agentic/gpt_bundle.py'...`).
- [x] `python3 tools/agentic/gpt_bundle.py --ticket ticket-12 --run-name 20260128_005626_ticket-ticket-12 --base-ref main`
  - Result: passed; wrote `artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip`.
- [x] Zip evidence checks:
  - `unzip -l artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip`
  - `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip changed_files.txt`
  - `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_20260212_230128_ticket-12.zip DIFF.patch | rg -n "scripts/reproduce_wrds_local_metrics\\.sh|tests/test_wrds_local_metrics_one_command_fast\\.py|docs/RUNBOOK\\.md|CMakeLists\\.txt|PROGRESS\\.md|docs/agent_runs/20260128_005626_ticket-ticket-12"`
  - Result: passed; bundle contains non-empty `DIFF.patch`, required file list, and run-log payload.
